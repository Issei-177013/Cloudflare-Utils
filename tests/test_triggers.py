import unittest
import os
import json
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.triggers import add_trigger, edit_trigger, delete_trigger
from src.background_service import _check_all_triggers
from src.ip_rotator import run_rotation
from src.logger import configure_console_logging, logger

class MockDNSRecord:
    def __init__(self, id, name, type, content):
        self.id = id
        self.name = name
        self.type = type
        self.content = content

class TestNewTriggers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Configure console logging for tests."""
        configure_console_logging({"logging": {"level": "DEBUG"}})

    def setUp(self):
        """No setup needed for file-based tests anymore."""
        pass

    def tearDown(self):
        """No teardown needed for file-based tests anymore."""
        pass

    @patch('src.triggers.select_from_list')
    @patch('src.triggers.get_user_input')
    @patch('src.triggers.get_validated_input')
    @patch('src.triggers.get_numeric_input')
    def test_add_trigger(self, mock_numeric, mock_validated, mock_user, mock_select):
        """Test the add_trigger function."""
        # --- Setup Mocks ---
        mock_config = {
            "agents": [{"name": "Test Agent", "url": "http://test.com", "api_key": "123"}]
        }
        mock_select.return_value = mock_config["agents"][0]
        mock_user.return_value = "Test Trigger"
        mock_validated.side_effect = ['1', '1'] # Period, Type
        mock_numeric.return_value = 100.0 # Volume

        # --- Call function ---
        new_trigger = add_trigger(mock_config)

        # --- Assertions ---
        self.assertIsNotNone(new_trigger)
        self.assertEqual(new_trigger["name"], "Test Trigger")
        self.assertEqual(new_trigger["agent_name"], "Test Agent")
        self.assertEqual(len(mock_config["triggers"]), 1)
        self.assertEqual(mock_config["triggers"][0]["name"], "Test Trigger")
        self.assertTrue(mock_config["triggers"][0]["alert_enabled"])

    @patch('src.background_service.logger')
    @patch('src.background_service.save_state')
    @patch('src.background_service.load_state')
    @patch('src.background_service.load_config')
    @patch('src.background_service._get_usage_for_period')
    def test_background_service_alerting(self, mock_get_usage, mock_load_config, mock_load_state, mock_save_state, mock_logger):
        """Test the background service's trigger evaluation and alerting logic."""
        # --- Test Case 1: Alerting Enabled (Default) ---
        trigger_alert_on = {"id": "trigger_alert_on", "name": "Alerting Trigger", "agent_name": "Test Agent BG", "period": "d", "volume_gb": 50, "volume_type": "total", "alert_enabled": True}
        agent = {"name": "Test Agent BG", "url": "http://test.com", "api_key": "123"}
        mock_load_config.return_value = {"agents": [agent], "triggers": [trigger_alert_on]}
        mock_load_state.return_value = {}
        mock_get_usage.return_value = {"total": 60 * (1024**3)}

        _check_all_triggers()

        mock_logger.warning.assert_called_with(f"🚨 ALERT: Trigger '{trigger_alert_on['name']}' has been activated. 🚨")
        mock_save_state.assert_called_once()
        saved_state = mock_save_state.call_args[0][0]
        self.assertIn(trigger_alert_on["id"], saved_state["fired_triggers"])

        # --- Reset mocks for next case ---
        mock_logger.reset_mock()
        mock_save_state.reset_mock()

        # --- Test Case 2: Alerting Disabled ---
        trigger_alert_off = {"id": "trigger_alert_off", "name": "Silent Trigger", "agent_name": "Test Agent BG", "period": "d", "volume_gb": 50, "volume_type": "total", "alert_enabled": False}
        mock_load_config.return_value = {"agents": [agent], "triggers": [trigger_alert_off]}
        mock_load_state.return_value = {} # Reset state

        _check_all_triggers()

        mock_logger.info.assert_any_call(f"Trigger '{trigger_alert_off['name']}' is silent. No alert sent.")
        mock_logger.warning.assert_not_called()
        mock_save_state.assert_called_once()
        saved_state = mock_save_state.call_args[0][0]
        self.assertIn(trigger_alert_off["id"], saved_state["fired_triggers"])


if __name__ == '__main__':
    unittest.main()
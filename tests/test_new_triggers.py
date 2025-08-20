import unittest
import os
import json
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.triggers import add_trigger, select_trigger
from src.background_service import _check_all_triggers
from src.ip_rotator import run_rotation
from src.logger import configure_console_logging

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

    @patch('src.triggers.save_config')
    @patch('src.triggers.load_config')
    @patch('src.triggers.select_from_list')
    @patch('src.triggers.get_user_input')
    @patch('src.triggers.get_validated_input')
    @patch('src.triggers.get_numeric_input')
    def test_select_trigger_create_new(self, mock_numeric, mock_validated, mock_user, mock_select, mock_load_config, mock_save_config):
        """Test the select_trigger function when creating a new trigger."""
        # --- Setup Mocks ---
        mock_user.side_effect = ['2', "New Test Trigger"]
        mock_load_config.return_value = {
            "agents": [{"name": "Test Agent", "url": "http://test.com", "api_key": "123"}], "triggers": []
        }
        mock_select.return_value = mock_load_config.return_value["agents"][0]
        mock_validated.side_effect = ['1', '1']
        mock_numeric.return_value = 100.0

        # --- Call function ---
        trigger_id = select_trigger()

        # --- Assertions ---
        self.assertIsNotNone(trigger_id)
        mock_save_config.assert_called_once()
        saved_config = mock_save_config.call_args[0][0]
        self.assertEqual(len(saved_config["triggers"]), 1)
        self.assertEqual(saved_config["triggers"][0]["id"], trigger_id)

    @patch('src.background_service.save_state')
    @patch('src.background_service.load_state')
    @patch('src.background_service.load_config')
    @patch('src.background_service._get_usage_for_period')
    def test_background_service_evaluation(self, mock_get_usage, mock_load_config, mock_load_state, mock_save_state):
        """Test the background service's trigger evaluation logic."""
        trigger = {"id": "trigger_test123", "name": "Test Trigger BG", "agent_name": "Test Agent BG", "period": "d", "volume_gb": 50, "volume_type": "total"}
        agent = {"name": "Test Agent BG", "url": "http://test.com", "api_key": "123"}
        mock_load_config.return_value = {"agents": [agent], "triggers": [trigger], "alarms": []}
        mock_load_state.return_value = {}
        mock_get_usage.return_value = {"total": 60 * (1024**3)}

        _check_all_triggers()

        mock_save_state.assert_called_once()
        saved_state = mock_save_state.call_args[0][0]
        self.assertIn("fired_triggers", saved_state)
        self.assertIn(trigger["id"], saved_state["fired_triggers"])

    @patch('src.ip_rotator.load_rotation_status')
    @patch('src.ip_rotator.save_state')
    @patch('src.ip_rotator.load_state')
    @patch('src.ip_rotator.load_config')
    @patch('src.ip_rotator.CloudflareAPI')
    def test_ip_rotator_with_trigger(self, MockCloudflareAPI, mock_load_config, mock_load_state, mock_save_state, mock_load_rotation_status):
        """Test that the IP rotator runs for a trigger-based schedule."""
        mock_api_instance = MockCloudflareAPI.return_value
        mock_api_instance.list_dns_records.return_value = [MockDNSRecord(id="rec_id_1", name="test.example.com", type="A", content="1.1.1.1")]
        
        trigger_id = "trigger_rotator123"
        schedule = {"type": "trigger", "trigger_id": trigger_id}
        record = {"name": "test.example.com", "type": "A", "ips": ["1.1.1.1", "2.2.2.2"], "schedule": schedule}
        zone = {"domain": "example.com", "zone_id": "zone_id_1", "records": [record]}
        account = {"name": "Test Account", "api_token": "dummy", "zones": [zone]}
        mock_load_config.return_value = {"accounts": [account]}
        mock_load_state.return_value = {"fired_triggers": {trigger_id: "2024-01-01T12:00:00"}}
        mock_load_rotation_status.return_value = {}

        run_rotation()

        mock_api_instance.update_dns_record.assert_called_once()
        mock_save_state.assert_called_once()
        saved_state = mock_save_state.call_args[0][0]
        self.assertNotIn(trigger_id, saved_state["fired_triggers"])

    @patch('src.ip_rotator.save_state')
    @patch('src.ip_rotator.load_state')
    @patch('src.ip_rotator.load_config')
    @patch('src.ip_rotator.CloudflareAPI')
    def test_ip_rotator_with_global_trigger(self, MockCloudflareAPI, mock_load_config, mock_load_state, mock_save_state):
        """Test that the IP rotator runs for a trigger-based global rotation."""
        mock_api_instance = MockCloudflareAPI.return_value
        mock_api_instance.list_dns_records.return_value = [
            MockDNSRecord(id="rec_id_1", name="global1.example.com", type="A", content="1.1.1.1"),
            MockDNSRecord(id="rec_id_2", name="global2.example.com", type="A", content="2.2.2.2"),
        ]
        
        trigger_id = "trigger_global123"
        schedule = {"type": "trigger", "trigger_id": trigger_id}
        global_rotation = {
            "account_name": "Test Account", "zone_id": "zone_id_1", "zone_name": "example.com",
            "records": ["global1.example.com", "global2.example.com"],
            "ip_pool": ["3.3.3.3", "4.4.4.4"],
            "schedule": schedule, "rotation_index": 0, "last_rotated_at": 0
        }
        mock_load_config.return_value = {"accounts": [{"name": "Test Account", "api_token": "dummy"}]}
        mock_load_state.return_value = {
            "global_rotations": {"Test Global": global_rotation},
            "fired_triggers": {trigger_id: "2024-01-01T12:00:00"}
        }

        run_rotation()

        self.assertEqual(mock_api_instance.update_dns_record.call_count, 2)
        mock_save_state.assert_called_once()
        saved_state = mock_save_state.call_args[0][0]
        self.assertNotIn(trigger_id, saved_state.get("fired_triggers", {}))

    @patch('src.ip_rotator.load_rotation_status')
    @patch('src.ip_rotator.save_state')
    @patch('src.ip_rotator.load_state')
    @patch('src.ip_rotator.load_config')
    @patch('src.ip_rotator.CloudflareAPI')
    def test_ip_rotator_with_group_trigger(self, MockCloudflareAPI, mock_load_config, mock_load_state, mock_save_state, mock_load_rotation_status):
        """Test that the IP rotator runs for a trigger-based group rotation."""
        mock_api_instance = MockCloudflareAPI.return_value
        mock_api_instance.list_dns_records.return_value = [
            MockDNSRecord(id="rec_id_1", name="group1.example.com", type="A", content="1.1.1.1"),
            MockDNSRecord(id="rec_id_2", name="group2.example.com", type="A", content="2.2.2.2"),
        ]

        trigger_id = "trigger_group123"
        schedule = {"type": "trigger", "trigger_id": trigger_id}
        rotation_group = {"name": "Test Group", "records": ["group1.example.com", "group2.example.com"], "schedule": schedule}
        zone = {"domain": "example.com", "zone_id": "zone_id_1", "rotation_groups": [rotation_group]}
        account = {"name": "Test Account", "api_token": "dummy", "zones": [zone]}
        mock_load_config.return_value = {"accounts": [account]}
        mock_load_state.return_value = {"fired_triggers": {trigger_id: "2024-01-01T12:00:00"}}
        mock_load_rotation_status.return_value = {}

        run_rotation()

        self.assertEqual(mock_api_instance.update_dns_record.call_count, 2)
        mock_save_state.assert_called_once()
        saved_state = mock_save_state.call_args[0][0]
        self.assertNotIn(trigger_id, saved_state.get("fired_triggers", {}))

    @patch('src.menus.consumption_alarms.save_config')
    @patch('src.menus.consumption_alarms.load_config')
    @patch('builtins.input')
    def test_add_alarm_flow(self, mock_input, mock_load_config, mock_save_config):
        """Test the new integrated 'add_alarm' workflow."""
        # --- Setup Mocks ---
        mock_load_config.return_value = {
            "agents": [{"name": "Test Agent", "url": "http://test.com", "api_key": "123"}],
            "triggers": [], "alarms": []
        }
        mock_input.side_effect = [
            "My New Alarm",     # Alarm name
            "1",                # Select agent
            "My New Trigger",   # Trigger name
            "1",                # Period
            "150.0",            # Volume
            "1",                # Volume type
            "",                 # Press enter in add_trigger
        ]

        # --- Call function ---
        from src.menus.consumption_alarms import add_alarm
        add_alarm()

        # --- Assertions ---
        mock_save_config.assert_called_once()
        saved_config = mock_save_config.call_args[0][0]

        self.assertEqual(len(saved_config["alarms"]), 1)
        self.assertEqual(saved_config["alarms"][0]["name"], "My New Alarm")
        
        self.assertEqual(len(saved_config["triggers"]), 1)
        self.assertEqual(saved_config["triggers"][0]["name"], "My New Trigger")
        
        # Check that the alarm is linked to the new trigger
        self.assertEqual(saved_config["alarms"][0]["trigger_id"], saved_config["triggers"][0]["id"])

    @patch('src.menus.consumption_alarms.save_config')
    @patch('src.menus.consumption_alarms.load_config')
    @patch('builtins.input')
    def test_add_alarm_for_self_monitor(self, mock_input, mock_load_config, mock_save_config):
        """Test creating an alarm for the self-monitor agent."""
        # --- Setup Mocks ---
        mock_load_config.return_value = {
            "agents": [], "triggers": [], "alarms": [],
            "self_monitor": {"enabled": True, "name": "My Local Machine"}
        }
        mock_input.side_effect = [
            "Self-Monitor Alarm", # Alarm name
            "1",                  # Select self-monitor agent
            "Self-Monitor Trigger", # Trigger name
            "1", "150.0", "1",    # Period, Volume, Type
            "",                   # Press enter
        ]

        # --- Call function ---
        from src.menus.consumption_alarms import add_alarm
        add_alarm()

        # --- Assertions ---
        mock_save_config.assert_called_once()
        saved_config = mock_save_config.call_args[0][0]

        self.assertEqual(len(saved_config["alarms"]), 1)
        self.assertEqual(saved_config["alarms"][0]["name"], "Self-Monitor Alarm")
        
        self.assertEqual(len(saved_config["triggers"]), 1)
        trigger = saved_config["triggers"][0]
        self.assertEqual(trigger["name"], "Self-Monitor Trigger")
        self.assertEqual(trigger["agent_name"], "My Local Machine")
        
        self.assertEqual(saved_config["alarms"][0]["trigger_id"], trigger["id"])


if __name__ == '__main__':
    unittest.main()
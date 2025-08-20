import unittest
import os
import json
from unittest.mock import patch, MagicMock

import sys
import time
# Add the 'src' directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.menus.traffic_monitoring import add_agent
from src.trigger_evaluator import check_triggers_for_agent

class TestTriggers(unittest.TestCase):

    def setUp(self):
        """No setup needed for file-based tests anymore."""
        pass

    def tearDown(self):
        """No teardown needed for file-based tests anymore."""
        pass

    @patch('builtins.input')
    @patch('src.menus.traffic_monitoring.save_config')
    @patch('src.menus.traffic_monitoring.load_config')
    def test_add_agent(self, mock_load_config, mock_save_config, mock_input):
        """Test adding an agent."""
        # --- Setup Mocks ---
        mock_load_config.return_value = {"agents": []}
        mock_input.side_effect = [
            'Test Agent',    # name
            '127.0.0.1',     # host
            '15728',         # port
            'TestAPIKey',    # api_key
            '',              # Press enter to continue
        ]

        # --- Call the function to test ---
        from src.menus.traffic_monitoring import add_agent
        add_agent()

        # --- Assertions ---
        mock_save_config.assert_called_once()
        saved_config = mock_save_config.call_args[0][0]
        
        self.assertEqual(len(saved_config['agents']), 1)
        agent = saved_config['agents'][0]
        self.assertEqual(agent['name'], 'Test Agent')
        self.assertEqual(agent['url'], 'http://127.0.0.1:15728')
        self.assertEqual(agent['api_key'], 'TestAPIKey')

    @patch('src.trigger_evaluator.save_state')
    @patch('src.trigger_evaluator.load_state')
    @patch('src.trigger_evaluator._get_usage_for_period')
    def test_trigger_evaluation_and_state(self, mock_get_usage, mock_load_state, mock_save_state):
        """Test that a trigger fires when usage is high and is recorded in state."""
        # --- Setup ---
        agent = {
            "name": "Test Agent Eval", "type": "remote", "url": "http://127.0.0.1:15728", "api_key": "TestAPIKey",
            "triggers": [{"name": "Test Trigger Eval", "period": "d", "volume_gb": 100, "volume_type": "rx", "action": "alarm"}]
        }
        mock_get_usage.return_value = {"rx": 150 * (1024**3), "tx": 10 * (1024**3), "total": 160 * (1024**3)}
        
        # --- First call: Trigger should fire ---
        mock_load_state.return_value = {} # Start with empty state
        from src.trigger_evaluator import check_triggers_for_agent
        check_triggers_for_agent(agent)

        # --- Assertions for first fire ---
        mock_save_state.assert_called_once()
        saved_state = mock_save_state.call_args[0][0]
        trigger_key = f"trigger_{agent['name']}_{agent['triggers'][0]['name']}"
        self.assertIn(trigger_key, saved_state)

        # --- Second call: Trigger should NOT fire again ---
        mock_load_state.return_value = saved_state # Next load will have the saved state
        mock_save_state.reset_mock() # Reset the mock for the next assertion
        
        check_triggers_for_agent(agent)
        
        mock_save_state.assert_not_called()


if __name__ == '__main__':
    unittest.main()
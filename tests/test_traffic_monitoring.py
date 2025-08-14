import unittest
import requests
from unittest.mock import patch, MagicMock
from src.ip_rotator import check_agent_traffic
from src.logger import logger

class TestTrafficMonitoring(unittest.TestCase):

    @patch('src.ip_rotator.requests.get')
    def test_check_agent_traffic_threshold_exceeded(self, mock_requests_get):
        """
        Tests that a warning is logged when agent traffic exceeds the threshold.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Simulate 600 GB in bytes
        mock_response.json.return_value = {
            "this_month": {"total_bytes": 600 * (1024**3)}
        }
        mock_requests_get.return_value = mock_response

        config = {
            "agents": [
                {
                    "name": "TestServer",
                    "url": "http://test-server:5000",
                    "api_key": "test-key",
                    "threshold_gb": 500
                }
            ]
        }

        # Act & Assert
        with self.assertLogs('CloudflareUtils', level='WARNING') as cm:
            check_agent_traffic(config)
            # Check that the logged message contains the expected warning
            output_str = "".join(cm.output)
            self.assertIn("TRAFFIC ALERT for agent 'TestServer'", output_str)
            self.assertIn("exceeds threshold", output_str)

    @patch('src.ip_rotator.requests.get')
    def test_check_agent_traffic_ok(self, mock_requests_get):
        """
        Tests that an info message is logged when traffic is within the threshold.
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Simulate 400 GB in bytes
        mock_response.json.return_value = {
            "this_month": {"total_bytes": 400 * (1024**3)}
        }
        mock_requests_get.return_value = mock_response

        config = {
            "agents": [
                {
                    "name": "TestServer",
                    "url": "http://test-server:5000",
                    "api_key": "test-key",
                    "threshold_gb": 500
                }
            ]
        }

        # Act & Assert
        # We expect two logs: one for starting the check, one for the result.
        with self.assertLogs('CloudflareUtils', level='INFO') as cm:
            check_agent_traffic(config)
            self.assertTrue(any("usage is OK" in msg for msg in cm.output))

    @patch('src.ip_rotator.requests.get')
    def test_check_agent_traffic_api_error(self, mock_requests_get):
        """
        Tests that an error is logged when the agent API returns an error.
        """
        # Arrange
        mock_requests_get.side_effect = requests.exceptions.RequestException("Test connection error")

        config = {
            "agents": [
                {
                    "name": "FailingServer",
                    "url": "http://fail-server:5000",
                    "api_key": "test-key",
                    "threshold_gb": 500
                }
            ]
        }

        # Act & Assert
        with self.assertLogs('CloudflareUtils', level='ERROR') as cm:
            check_agent_traffic(config)
            self.assertTrue(any("Could not connect to agent 'FailingServer'" in msg for msg in cm.output))

if __name__ == '__main__':
    unittest.main()
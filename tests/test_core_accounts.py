import unittest
from unittest.mock import patch, MagicMock
from src.core import accounts
from src.core.exceptions import ConfigError, AuthenticationError

class TestCoreAccounts(unittest.TestCase):

    @patch('src.core.accounts.config_manager')
    @patch('src.core.accounts.CloudflareAPI')
    def test_add_account_success(self, mock_cloudflare_api, mock_config_manager):
        """Test successful account addition."""
        # Arrange
        mock_config_manager.find_account.return_value = None
        mock_api_instance = mock_cloudflare_api.return_value
        mock_api_instance.verify_token.return_value = True
        
        config_data = {"accounts": []}
        mock_config_manager.get_config.return_value = config_data

        # Act
        result = accounts.add_account("test_account", "test_token")

        # Assert
        self.assertEqual(result["name"], "test_account")
        self.assertEqual(len(config_data["accounts"]), 1)
        mock_config_manager.save_config.assert_called_once()

    @patch('src.core.accounts.config_manager')
    def test_add_account_already_exists(self, mock_config_manager):
        """Test adding an account that already exists."""
        # Arrange
        mock_config_manager.find_account.return_value = {"name": "test_account"}

        # Act & Assert
        with self.assertRaises(ConfigError):
            accounts.add_account("test_account", "test_token")

    @patch('src.core.accounts.config_manager')
    @patch('src.core.accounts.CloudflareAPI')
    def test_add_account_auth_error(self, mock_cloudflare_api, mock_config_manager):
        """Test account addition with an authentication error."""
        # Arrange
        mock_config_manager.find_account.return_value = None
        mock_api_instance = mock_cloudflare_api.return_value
        mock_api_instance.verify_token.side_effect = AuthenticationError("Invalid token")

        # Act & Assert
        with self.assertRaises(AuthenticationError):
            accounts.add_account("test_account", "test_token")

    @patch('src.core.accounts.config_manager')
    def test_edit_account_success(self, mock_config_manager):
        """Test successful account editing."""
        # Arrange
        mock_account = {"name": "old_name", "api_token": "old_token"}
        mock_config_manager.find_account.return_value = mock_account

        # Act
        result = accounts.edit_account("old_name", new_name="new_name", new_token="new_token")

        # Assert
        self.assertTrue(result)
        self.assertEqual(mock_account["name"], "new_name")
        self.assertEqual(mock_account["api_token"], "new_token")
        mock_config_manager.save_config.assert_called_once()

    @patch('src.core.accounts.config_manager')
    def test_delete_account_success(self, mock_config_manager):
        """Test successful account deletion."""
        # Arrange
        mock_account = {"name": "test_account"}
        config_data = {"accounts": [mock_account]}
        mock_config_manager.get_config.return_value = config_data
        mock_config_manager.find_account.return_value = mock_account

        # Act
        result = accounts.delete_account("test_account")

        # Assert
        self.assertTrue(result)
        self.assertEqual(len(config_data["accounts"]), 0)
        mock_config_manager.save_config.assert_called_once()

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import patch
from src.core.app import Application
from src.core.exceptions import CoreError

class TestApplicationFacade(unittest.TestCase):

    def setUp(self):
        self.app = Application()

    @patch('src.core.app.accounts.get_accounts')
    def test_get_accounts_success(self, mock_get_accounts):
        """Test successful retrieval of accounts."""
        # Arrange
        mock_get_accounts.return_value = [{"name": "test1"}, {"name": "test2"}]

        # Act
        success, result = self.app.get_accounts()

        # Assert
        self.assertTrue(success)
        self.assertEqual(len(result), 2)
        mock_get_accounts.assert_called_once()

    @patch('src.core.app.accounts.get_accounts')
    def test_get_accounts_failure(self, mock_get_accounts):
        """Test failure in retrieving accounts."""
        # Arrange
        mock_get_accounts.side_effect = CoreError("Failed to load config")

        # Act
        success, result = self.app.get_accounts()

        # Assert
        self.assertFalse(success)
        self.assertEqual(result, "Failed to load config")

    @patch('src.core.app.accounts.add_account')
    def test_add_account_success(self, mock_add_account):
        """Test successful account addition."""
        # Arrange
        mock_add_account.return_value = {"name": "new_account"}

        # Act
        success, result = self.app.add_account("new_account", "new_token")

        # Assert
        self.assertTrue(success)
        self.assertEqual(result["name"], "new_account")
        mock_add_account.assert_called_once_with("new_account", "new_token")

    @patch('src.core.app.accounts.add_account')
    def test_add_account_failure(self, mock_add_account):
        """Test failure in adding an account."""
        # Arrange
        mock_add_account.side_effect = CoreError("Account already exists")

        # Act
        success, result = self.app.add_account("existing_account", "token")

        # Assert
        self.assertFalse(success)
        self.assertEqual(result, "Account already exists")

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
from src.menus.accounts import add_account_menu
from src.core.exceptions import APIError, AuthenticationError, ConfigError
from src.app import main

class TestApp(unittest.TestCase):

    @patch('src.menus.accounts.get_validated_input')
    @patch('src.menus.accounts.app.add_account')
    def test_add_account_valid_token(self, mock_add_account, mock_get_validated_input):
        # Arrange
        mock_get_validated_input.side_effect = ['test_account', 'valid_token']
        mock_add_account.return_value = (True, {"name": "test_account"})

        # Act
        add_account_menu()

        # Assert
        mock_add_account.assert_called_once_with('test_account', 'valid_token')


    @patch('src.app.config_manager')
    @patch('src.app.configure_console_logging')
    @patch('src.app.main_menu')
    def test_main_with_accounts(self, mock_main_menu, mock_configure_console_logging, mock_config_manager):
        # Arrange
        mock_config_manager.get_config.return_value = {"accounts": [{"name": "test_account"}]}

        # Act
        main()

        # Assert
        mock_main_menu.assert_called_once()

    @patch('src.app.config_manager')
    @patch('src.app.configure_console_logging')
    @patch('src.app.add_account_menu')
    @patch('src.app.main_menu')
    @patch('builtins.input')
    def test_main_no_accounts_then_add(self, mock_input, mock_main_menu, mock_add_account_menu, mock_configure_console_logging, mock_config_manager):
        # Arrange
        mock_config_manager.get_config.side_effect = [{"accounts": []}, {"accounts": [{"name": "new_account"}]}]

        # Act
        main()

        # Assert
        mock_add_account_menu.assert_called_once()
        mock_main_menu.assert_called_once()

if __name__ == '__main__':
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock
from src.menus.accounts import add_account
from cloudflare import APIError

class TestApp(unittest.TestCase):

    @patch('src.menus.accounts.get_validated_input')
    @patch('src.menus.accounts.CloudflareAPI')
    @patch('src.menus.accounts.confirm_action')
    @patch('src.menus.accounts.validate_and_save_config')
    @patch('src.menus.accounts.load_config')
    def test_add_account_valid_token(self, mock_load_config, mock_validate_and_save_config, mock_confirm_action, mock_cloudflare_api, mock_get_validated_input):
        # Arrange
        mock_get_validated_input.side_effect = ['test_account', 'valid_token']
        mock_load_config.return_value = {"accounts": []}
        mock_cloudflare_api.return_value.verify_token.return_value = None
        mock_validate_and_save_config.return_value = True

        # Act
        add_account()

        # Assert
        mock_cloudflare_api.assert_called_with('valid_token')
        mock_cloudflare_api.return_value.verify_token.assert_called_once()
        mock_validate_and_save_config.assert_called_once()

    @patch('src.menus.accounts.get_validated_input')
    @patch('src.menus.accounts.CloudflareAPI')
    @patch('src.menus.accounts.confirm_action')
    @patch('src.menus.accounts.validate_and_save_config')
    @patch('src.menus.accounts.load_config')
    def test_add_account_invalid_token_then_valid_token(self, mock_load_config, mock_validate_and_save_config, mock_confirm_action, mock_cloudflare_api, mock_get_validated_input):
        # Arrange
        mock_get_validated_input.side_effect = ['test_account', 'invalid_token', 'valid_token']
        mock_load_config.return_value = {"accounts": []}
        mock_cloudflare_api.side_effect = [MagicMock(verify_token=MagicMock(side_effect=APIError("Invalid token", request=MagicMock(), body=None))), MagicMock(verify_token=MagicMock())]
        mock_confirm_action.return_value = True
        mock_validate_and_save_config.return_value = True

        # Act
        add_account()

        # Assert
        self.assertEqual(mock_cloudflare_api.call_count, 2)
        mock_confirm_action.assert_called_once_with("Try again?")
        mock_validate_and_save_config.assert_called_once()

    @patch('src.menus.accounts.get_validated_input')
    @patch('src.menus.accounts.CloudflareAPI')
    @patch('src.menus.accounts.confirm_action')
    @patch('src.menus.accounts.validate_and_save_config')
    @patch('src.menus.accounts.load_config')
    def test_add_account_invalid_token_then_cancel(self, mock_load_config, mock_validate_and_save_config, mock_confirm_action, mock_cloudflare_api, mock_get_validated_input):
        # Arrange
        mock_get_validated_input.side_effect = ['test_account', 'invalid_token']
        mock_load_config.return_value = {"accounts": []}
        mock_cloudflare_api.return_value.verify_token.side_effect = APIError("Invalid token", request=MagicMock(), body=None)
        mock_confirm_action.return_value = False
        
        # Act
        add_account()

        # Assert
        mock_cloudflare_api.assert_called_with('invalid_token')
        mock_confirm_action.assert_called_once_with("Try again?")
        mock_validate_and_save_config.assert_not_called()

if __name__ == '__main__':
    unittest.main()
import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from telegram.constants import ChatType # type: ignore
from src.bot import handlers

class TestBotHandlers(unittest.TestCase):

    def setUp(self):
        """Set up the test environment."""
        self.update = MagicMock()
        self.update.effective_chat.type = ChatType.PRIVATE
        self.update.callback_query.answer = AsyncMock()
        self.update.callback_query.edit_message_text = AsyncMock()
        self.update.message.reply_text = AsyncMock()
        self.context = MagicMock()
        self.context.bot.send_message = AsyncMock()

    def test_button_handler_main_menu(self):
        """Test the button handler for the main menu."""
        self.update.callback_query.data = "menu_main"
        asyncio.run(handlers.button_handler(self.update, self.context))
        self.update.callback_query.edit_message_text.assert_called_once()
        self.assertIn("Choose an option:", self.update.callback_query.edit_message_text.call_args[0][0])

    @patch('src.bot.handlers.get_accounts')
    @patch('src.bot.handlers.accounts_menu')
    def test_button_handler_accounts_menu_success(self, mock_accounts_menu, mock_get_accounts):
        """Test the button handler for the accounts menu successfully."""
        self.update.callback_query.data = "menu_accounts"
        mock_get_accounts.return_value = [{"name": "test1"}]
        mock_accounts_menu.return_value = "accounts_menu_markup"

        asyncio.run(handlers.button_handler(self.update, self.context))

        mock_get_accounts.assert_called_once()
        mock_accounts_menu.assert_called_once_with([{"name": "test1"}], page=1, lang='en')
        self.update.callback_query.edit_message_text.assert_called_with(
            "Accounts:",
            reply_markup="accounts_menu_markup"
        )

    def test_private_chat_only(self):
        """Test that the handler exits early if not in a private chat."""
        self.update.effective_chat.type = ChatType.GROUP
        self.update.callback_query.data = "menu_main"

        asyncio.run(handlers.button_handler(self.update, self.context))

        self.update.callback_query.edit_message_text.assert_called_once_with("This command can only be used in private chats.")

    @patch('src.bot.handlers.config_manager')
    @patch('src.bot.handlers.get_account_details_menu')
    def test_button_handler_view_account_success(self, mock_details_menu, mock_config_manager):
        """Test the button handler for viewing an account successfully."""
        self.update.callback_query.data = "VIEW_ACCOUNT:test_account:1"
        mock_config_manager.find_account.return_value = {"name": "test_account"}
        mock_config_manager.get_bot_lang.return_value = "en"
        mock_details_menu.return_value = ("details_text", "details_markup")

        asyncio.run(handlers.button_handler(self.update, self.context))

        mock_config_manager.find_account.assert_called_once_with("test_account")
        mock_details_menu.assert_called_once_with({"name": "test_account"}, 1, 'en')
        self.update.callback_query.edit_message_text.assert_called_with(
            "details_text",
            reply_markup="details_markup",
            parse_mode="Markdown"
        )

    @patch('src.bot.handlers.get_edit_rename_menu')
    def test_button_handler_edit_account_start(self, mock_rename_menu):
        """Test starting the edit account wizard."""
        self.update.callback_query.data = "EDIT_ACCOUNT:test_account:1"
        self.context.user_data = {}
        mock_rename_menu.return_value = ("rename_text", "rename_markup")

        asyncio.run(handlers.button_handler(self.update, self.context))

        self.assertEqual(self.context.user_data['wizard_step'], 'awaiting_new_name')
        self.assertEqual(self.context.user_data['account_to_edit'], 'test_account')
        mock_rename_menu.assert_called_once_with("test_account", 1, 'en')
        self.update.callback_query.edit_message_text.assert_called_with(
            "rename_text",
            reply_markup="rename_markup"
        )

    @patch('src.bot.handlers.get_edit_token_menu')
    def test_button_handler_edit_skip_rename(self, mock_token_menu):
        """Test skipping the rename step."""
        self.update.callback_query.data = "EDIT_SKIP_RENAME:test_account:1"
        self.context.user_data = {'wizard_step': 'awaiting_new_name'}
        mock_token_menu.return_value = ("token_text", "token_markup")

        asyncio.run(handlers.button_handler(self.update, self.context))

        self.assertEqual(self.context.user_data['wizard_step'], 'awaiting_new_token')
        mock_token_menu.assert_called_once_with("test_account", 1, 'en')
        self.update.callback_query.edit_message_text.assert_called_with("token_text", reply_markup="token_markup")

    @patch('src.bot.handlers.edit_account')
    @patch('src.bot.handlers.config_manager')
    @patch('src.bot.handlers.get_edit_token_menu')
    def test_handle_wizard_input_rename_success(self, mock_token_menu, mock_config_manager, mock_edit_account):
        """Test successful rename input in the wizard."""
        self.update.message.text = "new_name"
        self.context.user_data = {'wizard_step': 'awaiting_new_name', 'account_to_edit': 'old_name', 'page': 1}
        mock_config_manager.find_account.return_value = None
        mock_token_menu.return_value = ("token_text", "token_markup")

        asyncio.run(handlers.handle_wizard_input(self.update, self.context))

        mock_edit_account.assert_called_once_with("old_name", new_name="new_name")
        self.assertEqual(self.context.user_data['wizard_step'], 'awaiting_new_token')
        self.assertEqual(self.context.user_data['account_to_edit'], 'new_name')
        self.context.bot.send_message.assert_called_once()

    @patch('src.bot.handlers.edit_account')
    @patch('src.bot.handlers.config_manager')
    @patch('src.bot.handlers.CloudflareAPI')
    @patch('src.bot.handlers.get_account_details_menu')
    def test_handle_wizard_input_token_success(self, mock_details_menu, mock_cf_api, mock_config_manager, mock_edit_account):
        """Test successful token input in the wizard."""
        self.update.message.text = "new_token"
        self.context.user_data = {'wizard_step': 'awaiting_new_token', 'account_to_edit': 'account_name', 'page': 1}
        mock_cf_api.return_value.verify_token.return_value = True
        mock_config_manager.find_account.return_value = {"name": "account_name"}
        mock_details_menu.return_value = ("details_text", "details_markup")

        asyncio.run(handlers.handle_wizard_input(self.update, self.context))

        mock_edit_account.assert_called_once_with("account_name", new_token="new_token")
        self.assertEqual(self.context.user_data, {}) # Should be cleared
        self.context.bot.send_message.assert_called_once()

if __name__ == '__main__':
    unittest.main()
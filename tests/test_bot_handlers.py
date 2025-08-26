import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from telegram.constants import ChatType
from src.bot import handlers

class TestBotHandlers(unittest.TestCase):

    def setUp(self):
        """Set up the test environment."""
        self.update = MagicMock()
        self.update.effective_chat.type = ChatType.PRIVATE
        self.update.callback_query.answer = AsyncMock()
        self.update.callback_query.edit_message_text = AsyncMock()
        self.context = MagicMock()

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

if __name__ == '__main__':
    unittest.main()
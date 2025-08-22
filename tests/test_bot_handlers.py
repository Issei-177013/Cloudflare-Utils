import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.bot import handlers

class TestBotHandlers(unittest.TestCase):

    def test_button_handler_main_menu(self):
        """Test the button handler for the main menu."""
        # Arrange
        update = MagicMock()
        update.callback_query.data = "menu_main"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        context = MagicMock()

        # Act
        asyncio.run(handlers.button_handler(update, context))

        # Assert
        update.callback_query.edit_message_text.assert_called_once()
        self.assertIn("Choose an option:", update.callback_query.edit_message_text.call_args[0][0])

    def test_button_handler_accounts_menu(self):
        """Test the button handler for the accounts menu."""
        # Arrange
        update = MagicMock()
        update.callback_query.data = "menu_accounts"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        context = MagicMock()

        # Act
        asyncio.run(handlers.button_handler(update, context))

        # Assert
        update.callback_query.edit_message_text.assert_called_once()
        self.assertIn("Accounts Menu:", update.callback_query.edit_message_text.call_args[0][0])

    @patch('src.bot.handlers.accounts_menu')
    def test_button_handler_accounts_list_success(self, mock_accounts_menu):
        """Test the button handler for listing accounts successfully."""
        # Arrange
        update = MagicMock()
        update.callback_query.data = "accounts_list"
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        
        context = MagicMock()
        context.application.app.get_accounts.return_value = (True, [{"name": "test1"}])
        
        mock_accounts_menu.return_value = "accounts_menu_markup"

        # Act
        asyncio.run(handlers.button_handler(update, context))

        # Assert
        update.callback_query.edit_message_text.assert_called_once_with(
            "Accounts:\n- test1",
            reply_markup="accounts_menu_markup"
        )

if __name__ == '__main__':
    unittest.main()
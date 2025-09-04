import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from src.bot.main import main, start
from src.core.config import config_manager

class TestStartHandler(unittest.TestCase):

    def setUp(self):
        config_manager.load_config(data=config_manager._get_default_config())

    @patch('src.bot.main.language_menu')
    def test_start_new_user(self, mock_language_menu):
        """Test the start handler for a new user."""
        update = AsyncMock()
        context = AsyncMock()
        update.effective_user.id = 456
        
        import asyncio
        asyncio.run(start(update, context))

        mock_language_menu.assert_called_once()
        update.message.reply_text.assert_called_with("Please select your language:", reply_markup=mock_language_menu.return_value)

    @patch('src.bot.main.main_menu')
    def test_start_existing_user(self, mock_main_menu):
        """Test the start handler for an existing user."""
        user_id = 123
        config_manager.set_bot_lang(user_id, 'en')
        
        update = AsyncMock()
        context = AsyncMock()
        update.effective_user.id = user_id
        
        import asyncio
        with patch('src.bot.i18n.t', return_value="Welcome to Cloudflare Utils Bot!"):
            asyncio.run(start(update, context))

        mock_main_menu.assert_called_once_with('en')
        update.message.reply_text.assert_called_with("Welcome to Cloudflare Utils Bot!", reply_markup=mock_main_menu.return_value)

class TestBotMain(unittest.TestCase):

    @patch('src.bot.main.ApplicationBuilder')
    @patch('src.bot.main.config_manager')
    def test_main_function(self, mock_config_manager, mock_app_builder):
        """Test the main function of the bot."""
        # Arrange
        mock_config_manager.get_config.return_value = {"settings": {"bot": {"enabled": True, "token": "fake_token"}}}
        
        # Mock the whole builder chain
        mock_builder = MagicMock()
        mock_app_builder.return_value = mock_builder
        mock_application = MagicMock()
        mock_builder.token.return_value.build.return_value = mock_application

        # Act
        main()

        # Assert
        mock_builder.token.assert_called_with("fake_token")
        self.assertTrue(mock_application.add_handler.called)
        mock_application.run_polling.assert_called_once()

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
from src.bot.main import main, start

class TestBotMain(unittest.TestCase):

    @patch('src.bot.main.ApplicationBuilder')
    @patch('src.bot.main.config_manager')
    def test_main_function(self, mock_config_manager, mock_app_builder):
        """Test the main function of the bot."""
        # Arrange
        mock_config_manager.get_config.return_value = {"bot": {"token": "fake_token"}}
        
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
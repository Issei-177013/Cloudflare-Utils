import unittest
from unittest.mock import patch, MagicMock
import datetime
from src.core.utils import format_datetime
from src.core.config import config_manager

class TestTimezone(unittest.TestCase):

    def setUp(self):
        # Reset config before each test
        config_manager.load_config(data=None)
        config_manager.config_data = config_manager._get_default_config()
        config_manager.save_config()

    def test_format_datetime_default_utc(self):
        """
        Tests if the format_datetime function uses UTC by default.
        """
        dt = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        formatted_dt = format_datetime(dt)
        self.assertIn("2023-01-01 12:00:00 UTC", formatted_dt)

    def test_format_datetime_custom_timezone(self):
        """
        Tests if the format_datetime function uses the timezone from the config.
        """
        # Set a custom timezone in the config
        config = config_manager.get_config()
        config["settings"]["global"]["timezone"] = "Europe/Berlin"
        config_manager.save_config()

        dt = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        formatted_dt = format_datetime(dt)

        # Berlin is UTC+1 in winter
        self.assertIn("2023-01-01 13:00:00", formatted_dt)

    def test_format_datetime_invalid_timezone(self):
        """
        Tests if the format_datetime function falls back to UTC for invalid timezones.
        """
        # Set an invalid timezone in the config
        config = config_manager.get_config()
        config["settings"]["global"]["timezone"] = "Mars/Olympus_Mons"
        config_manager.save_config()

        dt = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        formatted_dt = format_datetime(dt)
        self.assertIn("2023-01-01 12:00:00 UTC", formatted_dt)

    @patch('src.menus.settings.get_validated_input', return_value='Asia/Tehran')
    @patch('src.core.config.config_manager.save_config')
    def test_settings_menu_configure_timezone(self, mock_save_config, mock_get_input):
        """
        Tests the settings menu option for configuring the timezone.
        """
        config = config_manager.get_config()
        with patch('src.core.config.config_manager.get_config', return_value=config):
            with patch('builtins.input', side_effect=['1', '1', '\n', '0', '0']):
                from src.menus.settings import settings_menu
                settings_menu()

        mock_get_input.assert_called_once()
        mock_save_config.assert_called_once()
        self.assertEqual(config['settings']['global']['timezone'], 'Asia/Tehran')

    @patch('src.menus.settings.get_validated_input', return_value=None)
    @patch('src.menus.settings.config_manager.save_config')
    def test_settings_menu_invalid_timezone_input(self, mock_save_config, mock_get_input):
        """
        Tests that the settings menu handles invalid timezone input gracefully.
        """
        config = config_manager.get_config()
        with patch('src.core.config.config_manager.get_config', return_value=config):
            with patch('builtins.input', side_effect=['1', '1', '\n', '0', '0']):
                from src.menus.settings import settings_menu
                settings_menu()
        
        config = config_manager.get_config()
        self.assertEqual(config['settings']['global']['timezone'], 'UTC')
        mock_save_config.assert_not_called()

if __name__ == '__main__':
    unittest.main()
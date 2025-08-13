import unittest
from unittest.mock import patch, MagicMock
from src.menus.dns import dns_management_menu

@patch('src.config.logger')
@patch('src.menus.dns.logger')
@patch('src.menus.dns.display_as_table')
class TestDNSManager(unittest.TestCase):

    @patch('src.menus.dns.load_config')
    @patch('src.menus.dns.CloudflareAPI')
    @patch('src.menus.dns.select_from_list')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_list_dns_records(self, mock_print, mock_input, mock_select, mock_cf_api, mock_load_config, mock_display_as_table, mock_dns_logger, mock_config_logger):
        # Mock config
        mock_load_config.return_value = {
            "accounts": [{"name": "test_account", "api_token": "test_token"}]
        }

        # Mock CloudflareAPI instance and its methods
        mock_api_instance = MagicMock()
        mock_cf_api.return_value = mock_api_instance
        
        # Mock zones and records
        mock_zone = MagicMock()
        mock_zone.id = "zone123"
        mock_zone.name = "example.com"
        mock_api_instance.list_zones.return_value = [mock_zone]

        mock_record = MagicMock()
        mock_record.id = "rec123"
        mock_record.type = "A"
        mock_record.name = "www"
        mock_record.content = "1.1.1.1"
        mock_record.ttl = 3600
        mock_record.proxied = True
        mock_api_instance.list_dns_records.return_value = [mock_record]

        # Simulate user input
        mock_input.side_effect = ["1", "0", "0"] # Select zone, then exit, then exit main loop
        mock_select.return_value = {"name": "test_account", "api_token": "test_token"}

        # Run the menu
        dns_management_menu()

        # Assertions
        mock_api_instance.list_zones.assert_called_once()
        mock_api_instance.list_dns_records.assert_called_once_with("zone123")

    @patch('src.menus.dns.load_config')
    @patch('src.menus.dns.CloudflareAPI')
    @patch('src.menus.dns.select_from_list')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_add_dns_record(self, mock_print, mock_input, mock_select, mock_cf_api, mock_load_config, mock_display_as_table, mock_dns_logger, mock_config_logger):
        # Mock config
        mock_load_config.return_value = {
            "accounts": [{"name": "test_account", "api_token": "test_token"}]
        }

        # Mock CloudflareAPI instance and its methods
        mock_api_instance = MagicMock()
        mock_cf_api.return_value = mock_api_instance
        
        # Mock zones
        mock_zone = MagicMock()
        mock_zone.id = "zone123"
        mock_zone.name = "example.com"
        mock_api_instance.list_zones.return_value = [mock_zone]
        mock_api_instance.list_dns_records.return_value = []


        # Simulate user input
        mock_input.side_effect = ["1", "1", "A", "test", "1.2.3.4", "3600", "yes", "", "0", "0"] # Select zone, add record, enter details, then exit
        mock_select.return_value = {"name": "test_account", "api_token": "test_token"}

        # Run the menu
        dns_management_menu()

        # Assertions
        mock_api_instance.create_dns_record.assert_called_once_with('zone123', 'test', 'A', '1.2.3.4', True, 3600)

    @patch('src.menus.dns.load_config')
    @patch('src.menus.dns.CloudflareAPI')
    @patch('src.menus.dns.select_from_list')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_edit_dns_record(self, mock_print, mock_input, mock_select, mock_cf_api, mock_load_config, mock_display_as_table, mock_dns_logger, mock_config_logger):
        # Mock config
        mock_load_config.return_value = {
            "accounts": [{"name": "test_account", "api_token": "test_token"}]
        }

        # Mock CloudflareAPI instance and its methods
        mock_api_instance = MagicMock()
        mock_cf_api.return_value = mock_api_instance
        
        # Mock zones and records
        mock_zone = MagicMock()
        mock_zone.id = "zone123"
        mock_zone.name = "example.com"
        mock_api_instance.list_zones.return_value = [mock_zone]

        mock_record = MagicMock()
        mock_record.id = "rec123"
        mock_record.type = "A"
        mock_record.name = "www"
        mock_record.content = "1.1.1.1"
        mock_record.ttl = 3600
        mock_record.proxied = True
        mock_api_instance.list_dns_records.return_value = [mock_record]

        # Simulate user input
        mock_input.side_effect = ["1", "2", "1", "new_name", "CNAME", "new.content", "1800", "no", "", "0", "0"]
        mock_select.return_value = {"name": "test_account", "api_token": "test_token"}

        # Run the menu
        dns_management_menu()

        # Assertions
        mock_api_instance.update_dns_record.assert_called_once_with("zone123", "rec123", "new_name", "CNAME", "new.content", False, 1800)

    @patch('src.menus.dns.load_config')
    @patch('src.menus.dns.CloudflareAPI')
    @patch('src.menus.dns.select_from_list')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_delete_dns_record(self, mock_print, mock_input, mock_select, mock_cf_api, mock_load_config, mock_display_as_table, mock_dns_logger, mock_config_logger):
        # Mock config
        mock_load_config.return_value = {
            "accounts": [{"name": "test_account", "api_token": "test_token"}]
        }

        # Mock CloudflareAPI instance and its methods
        mock_api_instance = MagicMock()
        mock_cf_api.return_value = mock_api_instance
        
        # Mock zones and records
        mock_zone = MagicMock()
        mock_zone.id = "zone123"
        mock_zone.name = "example.com"
        mock_api_instance.list_zones.return_value = [mock_zone]

        mock_record = MagicMock()
        mock_record.id = "rec123"
        mock_record.type = "A"
        mock_record.name = "www"
        mock_record.content = "1.1.1.1"
        mock_record.ttl = 3600
        mock_record.proxied = True
        mock_api_instance.list_dns_records.return_value = [mock_record]

        # Simulate user input
        mock_input.side_effect = ["1", "3", "1", "www", "", "0", "0"]
        mock_select.return_value = {"name": "test_account", "api_token": "test_token"}

        # Run the menu
        dns_management_menu()

        # Assertions
        mock_api_instance.delete_dns_record.assert_called_once_with("zone123", "rec123")

if __name__ == '__main__':
    unittest.main()
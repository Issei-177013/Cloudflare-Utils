import unittest
from unittest.mock import patch, MagicMock
from src.menus.dns import dns_management_menu

@patch('src.menus.dns.logger')
@patch('src.menus.dns.display_as_table')
class TestDNSManager(unittest.TestCase):

    @patch('src.menus.dns.core_zones.list_zones')
    @patch('src.menus.dns.core_dns.list_dns_records')
    @patch('src.menus.dns.select_from_list')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_list_dns_records(self, mock_print, mock_input, mock_select, mock_list_dns_records, mock_list_zones, mock_display_as_table, mock_dns_logger):
        with patch('src.menus.dns.core_accounts.get_accounts') as mock_get_accounts:
            mock_get_accounts.return_value = [{"name": "test_account", "api_token": "test_token"}]
            mock_zone = MagicMock()
            mock_zone.id = "zone123"
            mock_zone.name = "example.com"
            mock_list_zones.return_value = [mock_zone]
            mock_record = MagicMock()
            mock_record.id = "rec123"
            mock_record.type = "A"
            mock_record.name = "www"
            mock_record.content = "1.1.1.1"
            mock_record.ttl = 3600
            mock_record.proxied = True
            mock_list_dns_records.return_value = [mock_record]
            mock_input.side_effect = ["1", "0", "0"]
            mock_select.return_value = {"name": "test_account", "api_token": "test_token"}

            dns_management_menu()

            mock_list_zones.assert_called_once()
            mock_list_dns_records.assert_called_once_with("test_token", "zone123")

    @patch('src.menus.dns.core_zones.list_zones')
    @patch('src.menus.dns.core_dns.list_dns_records')
    @patch('src.menus.dns.core_dns.create_dns_record')
    @patch('src.menus.dns.select_from_list')
    @patch('src.menus.dns.get_validated_input')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_add_dns_record(self, mock_print, mock_input, mock_get_validated_input, mock_select, mock_create_dns_record, mock_list_dns_records, mock_list_zones, mock_display_as_table, mock_dns_logger):
        with patch('src.menus.dns.core_accounts.get_accounts') as mock_get_accounts:
            mock_get_accounts.return_value = [{"name": "test_account", "api_token": "test_token"}]
            mock_zone = MagicMock()
            mock_zone.id = "zone123"
            mock_zone.name = "example.com"
            mock_list_zones.return_value = [mock_zone]
            mock_list_dns_records.return_value = []
            mock_get_validated_input.side_effect = ["A", "test", "1.2.3.4", "yes"]
            mock_input.side_effect = ["1", "1", "3600", "", "0", "0"]
            mock_select.return_value = {"name": "test_account", "api_token": "test_token"}

            dns_management_menu()

            mock_create_dns_record.assert_called_once_with("test_token", 'zone123', 'test', 'A', '1.2.3.4', True, 3600)

    @patch('src.menus.dns.core_zones.list_zones')
    @patch('src.menus.dns.core_dns.list_dns_records')
    @patch('src.menus.dns.core_dns.update_dns_record')
    @patch('src.menus.dns.select_from_list')
    @patch('src.menus.dns.get_validated_input')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_edit_dns_record(self, mock_print, mock_input, mock_get_validated_input, mock_select, mock_update_dns_record, mock_list_dns_records, mock_list_zones, mock_display_as_table, mock_dns_logger):
        with patch('src.menus.dns.core_accounts.get_accounts') as mock_get_accounts:
            mock_get_accounts.return_value = [{"name": "test_account", "api_token": "test_token"}]
            mock_zone = MagicMock()
            mock_zone.id = "zone123"
            mock_zone.name = "example.com"
            mock_list_zones.return_value = [mock_zone]
            mock_record = MagicMock()
            mock_record.id = "rec123"
            mock_record.type = "A"
            mock_record.name = "www"
            mock_record.content = "1.1.1.1"
            mock_record.ttl = 3600
            mock_record.proxied = True
            mock_list_dns_records.return_value = [mock_record]
            mock_get_validated_input.side_effect = ["CNAME", "no"]
            mock_input.side_effect = ["1", "2", "1", "new_name", "new.content", "1800", "", "0", "0"]
            mock_select.return_value = {"name": "test_account", "api_token": "test_token"}

            dns_management_menu()

            mock_update_dns_record.assert_called_once_with("test_token", "zone123", "rec123", "new_name", "CNAME", "new.content", False, 1800)

    @patch('src.menus.dns.core_zones.list_zones')
    @patch('src.menus.dns.core_dns.list_dns_records')
    @patch('src.menus.dns.core_dns.delete_dns_record')
    @patch('src.menus.dns.select_from_list')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_delete_dns_record(self, mock_print, mock_input, mock_select, mock_delete_dns_record, mock_list_dns_records, mock_list_zones, mock_display_as_table, mock_dns_logger):
        with patch('src.menus.dns.core_accounts.get_accounts') as mock_get_accounts:
            mock_get_accounts.return_value = [{"name": "test_account", "api_token": "test_token"}]
            mock_zone = MagicMock()
            mock_zone.id = "zone123"
            mock_zone.name = "example.com"
            mock_list_zones.return_value = [mock_zone]
            mock_record = MagicMock()
            mock_record.id = "rec123"
            mock_record.type = "A"
            mock_record.name = "www"
            mock_record.content = "1.1.1.1"
            mock_record.ttl = 3600
            mock_record.proxied = True
            mock_list_dns_records.return_value = [mock_record]
            mock_input.side_effect = ["1", "3", "1", "www", "", "0", "0"]
            mock_select.return_value = {"name": "test_account", "api_token": "test_token"}

            dns_management_menu()

            mock_delete_dns_record.assert_called_once_with("test_token", "zone123", "rec123")

if __name__ == '__main__':
    unittest.main()
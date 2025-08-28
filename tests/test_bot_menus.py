import unittest
from src.bot.menus import main, accounts, dns, zones, firewall, settings

class TestBotMenus(unittest.TestCase):

    def test_main_menu(self):
        """Test the main menu creation."""
        menu = main.main_menu()
        self.assertEqual(len(menu.inline_keyboard), 5)
        self.assertEqual(menu.inline_keyboard[0][0].text, "Accounts")

    def test_accounts_menu_with_accounts(self):
        """Test the accounts menu creation with accounts."""
        accs = [{"name": "test1"}, {"name": "test2"}]
        menu = accounts.accounts_menu(accs)
        # 2 accounts + Add Account + Back
        self.assertEqual(len(menu.inline_keyboard), 4)
        self.assertIn("test1", menu.inline_keyboard[0][0].text)

    def test_accounts_menu_empty(self):
        """Test the accounts menu with no accounts."""
        menu = accounts.accounts_menu([])
        # Add Account + Back
        self.assertEqual(len(menu.inline_keyboard), 2)
        self.assertEqual(menu.inline_keyboard[0][0].text, "➕ Add Account")

    def test_accounts_menu_pagination(self):
        """Test the accounts menu with pagination."""
        accs = [{"name": f"test{i}"} for i in range(15)]
        menu = accounts.accounts_menu(accs, page=1)
        # 10 accounts + Add Account + Pagination + Back
        self.assertEqual(len(menu.inline_keyboard), 13)
        # Pagination row is at index 11, Next button is at index 1 (0 is page indicator)
        self.assertEqual(menu.inline_keyboard[11][1].callback_data, "ACCOUNTS_PAGE:2")

    def test_get_account_details_menu(self):
        """Test the account details menu creation with and without email."""
        # Case 1: With email
        details_with_email = {"name": "test_account", "email": "test@example.com", "api_token": "test_token"}
        text, menu, parse_mode = accounts.get_account_details_menu(details_with_email, page=2)

        self.assertIn("test_account", text)
        self.assertIn("test_token", text)
        self.assertEqual(len(menu.inline_keyboard), 1)
        self.assertEqual(menu.inline_keyboard[0][0].callback_data, "ACCOUNTS_PAGE:2")
        self.assertEqual(parse_mode, "HTML")

        # Case 2: Without email
        details_without_email = {"name": "test_account", "email": None, "api_token": "test_token"}
        text, menu, parse_mode = accounts.get_account_details_menu(details_without_email, page=3)

        self.assertIn("test_account", text)
        self.assertIn("test_token", text)
        self.assertEqual(len(menu.inline_keyboard), 1)
        self.assertEqual(menu.inline_keyboard[0][0].callback_data, "ACCOUNTS_PAGE:3")
        self.assertEqual(parse_mode, "HTML")

    def test_get_edit_rename_menu(self):
        """Test the edit rename menu creation."""
        text, menu = accounts.get_edit_rename_menu("test_account", 1)
        self.assertIn("test_account", text)
        self.assertEqual(len(menu.inline_keyboard), 1)
        self.assertEqual(menu.inline_keyboard[0][0].callback_data, "EDIT_SKIP_RENAME:test_account:1")
        self.assertEqual(menu.inline_keyboard[0][1].callback_data, "EDIT_CANCEL:test_account:1")

    def test_get_edit_token_menu(self):
        """Test the edit token menu creation."""
        text, menu = accounts.get_edit_token_menu("test_account", 1)
        self.assertIn("new API token", text)
        self.assertEqual(len(menu.inline_keyboard), 1)
        self.assertEqual(menu.inline_keyboard[0][0].callback_data, "EDIT_SKIP_TOKEN:test_account:1")
        self.assertEqual(menu.inline_keyboard[0][1].callback_data, "EDIT_BACK_TO_RENAME:test_account:1")

    def test_dns_menu(self):
        """Test the dns menu creation."""
        menu = dns.dns_menu()
        self.assertEqual(len(menu.inline_keyboard), 5)
        self.assertEqual(menu.inline_keyboard[0][0].text, "List Records")

    def test_zones_menu(self):
        """Test the zones menu creation."""
        menu = zones.zones_menu()
        self.assertEqual(len(menu.inline_keyboard), 4)
        self.assertEqual(menu.inline_keyboard[0][0].text, "List Zones")

    def test_firewall_menu(self):
        """Test the firewall menu creation."""
        menu = firewall.firewall_menu()
        self.assertEqual(len(menu.inline_keyboard), 4)
        self.assertEqual(menu.inline_keyboard[0][0].text, "List Rules")

    def test_settings_menu(self):
        """Test the settings menu creation."""
        menu = settings.settings_menu()
        self.assertEqual(len(menu.inline_keyboard), 4)
        self.assertEqual(menu.inline_keyboard[0][0].text, "Language")

if __name__ == '__main__':
    unittest.main()
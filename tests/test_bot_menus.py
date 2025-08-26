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
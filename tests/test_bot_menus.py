import unittest
from src.bot.menus import main, accounts, dns, zones, firewall, settings

class TestBotMenus(unittest.TestCase):

    def test_main_menu(self):
        """Test the main menu creation."""
        menu = main.main_menu()
        self.assertEqual(len(menu.inline_keyboard), 5)
        self.assertEqual(menu.inline_keyboard[0][0].text, "Accounts")

    def test_accounts_menu(self):
        """Test the accounts menu creation."""
        menu = accounts.accounts_menu()
        self.assertEqual(len(menu.inline_keyboard), 4)
        self.assertEqual(menu.inline_keyboard[0][0].text, "List Accounts")

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
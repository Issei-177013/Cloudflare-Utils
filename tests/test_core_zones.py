import unittest
from unittest.mock import patch, MagicMock
from src.core import zones

class TestCoreZones(unittest.TestCase):

    @patch('src.core.zones.CloudflareAPI')
    def test_list_zones(self, mock_cloudflare_api):
        """Test listing zones."""
        # Arrange
        mock_api_instance = mock_cloudflare_api.return_value
        mock_api_instance.list_zones.return_value = [{"id": "1", "name": "example.com"}]

        # Act
        zone_list = zones.list_zones("fake_token")

        # Assert
        self.assertEqual(len(zone_list), 1)
        self.assertEqual(zone_list[0]["name"], "example.com")
        mock_api_instance.list_zones.assert_called_once()

    @patch('src.core.zones.CloudflareAPI')
    def test_get_zone_details(self, mock_cloudflare_api):
        """Test getting zone details."""
        # Arrange
        mock_api_instance = mock_cloudflare_api.return_value
        mock_api_instance.get_zone_details.return_value = {"id": "1", "name": "example.com", "status": "active"}

        # Act
        details = zones.get_zone_details("fake_token", "zone1")

        # Assert
        self.assertEqual(details["status"], "active")
        mock_api_instance.get_zone_details.assert_called_once_with("zone1")

    @patch('src.core.zones.CloudflareAPI')
    def test_add_zone(self, mock_cloudflare_api):
        """Test adding a zone."""
        # Arrange
        mock_api_instance = mock_cloudflare_api.return_value
        mock_api_instance.add_zone.return_value = {"id": "2", "name": "newzone.com"}

        # Act
        new_zone = zones.add_zone("fake_token", "newzone.com", zone_type="full")

        # Assert
        self.assertEqual(new_zone["name"], "newzone.com")
        mock_api_instance.add_zone.assert_called_once_with("newzone.com", zone_type="full")

    @patch('src.core.zones.CloudflareAPI')
    def test_delete_zone(self, mock_cloudflare_api):
        """Test deleting a zone."""
        # Arrange
        mock_api_instance = mock_cloudflare_api.return_value

        # Act
        zones.delete_zone("fake_token", "zone1")

        # Assert
        mock_api_instance.delete_zone.assert_called_once_with("zone1")

if __name__ == '__main__':
    unittest.main()
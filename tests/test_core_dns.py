import unittest
from unittest.mock import patch, MagicMock
from src.core import dns

class TestCoreDns(unittest.TestCase):

    @patch('src.core.dns.CloudflareAPI')
    def test_list_dns_records(self, mock_cloudflare_api):
        """Test listing DNS records."""
        # Arrange
        mock_api_instance = mock_cloudflare_api.return_value
        mock_api_instance.list_dns_records.return_value = [{"id": "1", "name": "example.com"}]

        # Act
        records = dns.list_dns_records("fake_token", "zone1")

        # Assert
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["name"], "example.com")
        mock_api_instance.list_dns_records.assert_called_once_with("zone1")

    @patch('src.core.dns.CloudflareAPI')
    def test_create_dns_record(self, mock_cloudflare_api):
        """Test creating a DNS record."""
        # Arrange
        mock_api_instance = mock_cloudflare_api.return_value
        mock_api_instance.create_dns_record.return_value = {"id": "2", "name": "new.example.com"}

        # Act
        record = dns.create_dns_record(
            "fake_token", "zone1", "new.example.com", "A", "1.1.1.1"
        )

        # Assert
        self.assertEqual(record["name"], "new.example.com")
        mock_api_instance.create_dns_record.assert_called_once_with(
            "zone1", "new.example.com", "A", "1.1.1.1", False, None
        )

    @patch('src.core.dns.CloudflareAPI')
    def test_update_dns_record(self, mock_cloudflare_api):
        """Test updating a DNS record."""
        # Arrange
        mock_api_instance = mock_cloudflare_api.return_value

        # Act
        dns.update_dns_record(
            "fake_token", "zone1", "rec1", "edit.example.com", "A", "2.2.2.2", True, 300
        )

        # Assert
        mock_api_instance.update_dns_record.assert_called_once_with(
            "zone1", "rec1", "edit.example.com", "A", "2.2.2.2", True, 300
        )

    @patch('src.core.dns.CloudflareAPI')
    def test_delete_dns_record(self, mock_cloudflare_api):
        """Test deleting a DNS record."""
        # Arrange
        mock_api_instance = mock_cloudflare_api.return_value

        # Act
        dns.delete_dns_record("fake_token", "zone1", "rec1")

        # Assert
        mock_api_instance.delete_dns_record.assert_called_once_with("zone1", "rec1")

if __name__ == '__main__':
    unittest.main()
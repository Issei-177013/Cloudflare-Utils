import unittest
from unittest.mock import MagicMock
from src.ip_rotator import rotate_ips_for_multi_record

class TestIpRotator(unittest.TestCase):

    def test_rotate_ips_for_multi_record_index_advancement(self):
        """
        Tests that the rotation index for multi-record rotation advances correctly.
        """
        # Arrange
        # Mock 3 DNS records
        records = [
            MagicMock(name='a.example.com', content='1.1.1.1', id='rec-id-1', type='A'),
            MagicMock(name='b.example.com', content='1.1.1.2', id='rec-id-2', type='A'),
            MagicMock(name='c.example.com', content='1.1.1.3', id='rec-id-3', type='A')
        ]
        ip_pool = ['10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.5']
        initial_rotation_index = 0

        # Act
        updated_records, new_rotation_index = rotate_ips_for_multi_record(
            records,
            ip_pool,
            initial_rotation_index
        )

        # Assert
        # The function should assign the first 3 IPs from the pool to the 3 records.
        self.assertEqual(len(updated_records), 3)
        self.assertEqual(updated_records[0]['new_ip'], '10.0.0.1')
        self.assertEqual(updated_records[1]['new_ip'], '10.0.0.2')
        self.assertEqual(updated_records[2]['new_ip'], '10.0.0.3')

        # The new index should point to the next IP in the pool for a sliding window rotation.
        # With the fix, the new logic is `(0 + 1) % 5 = 1`.
        expected_new_index = 1
        self.assertEqual(new_rotation_index, expected_new_index, "The rotation index should advance by 1 for the next rotation.")

if __name__ == '__main__':
    unittest.main()

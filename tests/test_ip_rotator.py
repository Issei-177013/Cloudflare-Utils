import unittest
from unittest.mock import MagicMock
from src.ip_rotator import rotate_ips_for_multi_record

class TestIpRotator(unittest.TestCase):

    def test_rotate_ips_for_multi_record(self):
        # Mock DNS records
        class MockRecord:
            def __init__(self, name, content, id, type='A'):
                self.name = name
                self.content = content
                self.id = id
                self.type = type

        records = [
            MockRecord("a.com", "1.1.1.1", "1"),
            MockRecord("b.com", "2.2.2.2", "2"),
            MockRecord("c.com", "3.3.3.3", "3"),
        ]
        
        ip_pool = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4", "10.0.0.5"]
        
        # --- Test Case 1: Initial rotation (index 0) ---
        rotation_index = 0
        updated, new_index = rotate_ips_for_multi_record(records, ip_pool, rotation_index)
        
        self.assertEqual(len(updated), 3)
        self.assertEqual(new_index, 4) # 0 - 1 -> -1, wraps to 4
        
        self.assertEqual(updated[0]['new_ip'], "10.0.0.1") # index 0
        self.assertEqual(updated[1]['new_ip'], "10.0.0.2") # index 1
        self.assertEqual(updated[2]['new_ip'], "10.0.0.3") # index 2

        # --- Test Case 2: Subsequent rotation (index 4) ---
        rotation_index = new_index # 4
        records[0].content = "10.0.0.1"
        records[1].content = "10.0.0.2"
        records[2].content = "10.0.0.3"
        updated, new_index = rotate_ips_for_multi_record(records, ip_pool, rotation_index)
        
        self.assertEqual(len(updated), 3)
        self.assertEqual(new_index, 3) # 4 - 1 -> 3

        self.assertEqual(updated[0]['new_ip'], "10.0.0.5") # index (4+0)%5 = 4
        self.assertEqual(updated[1]['new_ip'], "10.0.0.1") # index (4+1)%5 = 0
        self.assertEqual(updated[2]['new_ip'], "10.0.0.2") # index (4+2)%5 = 1

        # --- Test Case 3: No change needed ---
        rotation_index = 1
        records[0].content = "10.0.0.2" # (1+0)%5 = 1
        records[1].content = "10.0.0.3" # (1+1)%5 = 2
        records[2].content = "10.0.0.4" # (1+2)%5 = 3
        updated, new_index = rotate_ips_for_multi_record(records, ip_pool, rotation_index)

        self.assertEqual(len(updated), 0) # No records should be updated
        self.assertEqual(new_index, 0) # 1 - 1 -> 0

if __name__ == '__main__':
    unittest.main()

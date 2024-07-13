import os
import pytest
from unittest.mock import patch
from change_dns import ip_rotation

def test_ip_rotation():
    with patch.dict('os.environ', {'CLOUDFLARE_IP_ADDRESSES': '1.1.1.1,2.2.2.2,3.3.3.3'}):
        assert ip_rotation('1.1.1.1') == '2.2.2.2'
        assert ip_rotation('2.2.2.2') == '3.3.3.3'
        assert ip_rotation('3.3.3.3') == '1.1.1.1'
        assert ip_rotation('4.4.4.4') == '1.1.1.1'

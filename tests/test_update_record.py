import pytest
from unittest.mock import patch
from change_dns import update_record

@patch('change_dns.cf.dns.records.update')
def test_update_record(mock_update):
    mock_update.return_value = None  # Simulate successful update
    update_record('record_id', '2.3.4.5', 'A', 'example.com')
    mock_update.assert_called_with(
        dns_record_id='record_id',
        zone_id='zone_id',
        type='A',
        name='example.com',
        content='2.3.4.5',
        id='record_id',
    )

@patch('change_dns.cf.dns.records.update')
def test_update_record_api_error(mock_update):
    mock_update.side_effect = Exception('API Error')
    with pytest.raises(Exception):
        update_record('record_id', '2.3.4.5', 'A', 'example.com')

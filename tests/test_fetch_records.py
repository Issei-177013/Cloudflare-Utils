import os
import pytest
from unittest.mock import patch
from change_dns import fetch_records

@patch('change_dns.cf.dns.records.list')
def test_fetch_records(mock_list):
    mock_list.return_value.to_json.return_value = '{"result": [{"id": "record_id", "name": "example.com", "content": "1.2.3.4"}]}'
    os.environ['CLOUDFLARE_ZONE_ID'] = 'zone_id'
    records = fetch_records()
    assert len(records['result']) == 1
    assert records['result'][0]['id'] == 'record_id'
    assert records['result'][0]['name'] == 'example.com'
    assert records['result'][0]['content'] == '1.2.3.4'

@patch('change_dns.cf.dns.records.list')
def test_fetch_records_api_error(mock_list):
    mock_list.side_effect = Exception('API Error')
    os.environ['CLOUDFLARE_ZONE_ID'] = 'zone_id'
    records = fetch_records()
    assert records is None

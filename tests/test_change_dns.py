# Copyright 2024 [Issei-177013]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pytest
from unittest.mock import patch, MagicMock
from change_dns import fetch_records, update_record, ip_rotation

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

def test_ip_rotation():
    with patch.dict('os.environ', {'CLOUDFLARE_IP_ADDRESSES': '1.1.1.1,2.2.2.2,3.3.3.3'}):
        assert ip_rotation('1.1.1.1') == '2.2.2.2'
        assert ip_rotation('2.2.2.2') == '3.3.3.3'
        assert ip_rotation('3.3.3.3') == '1.1.1.1'
        assert ip_rotation('4.4.4.4') == '1.1.1.1'

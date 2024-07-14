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
from unittest.mock import patch
from change_dns import fetch_records, update_record, ip_rotation

@patch('change_dns.cf.dns.records.list')
@patch('change_dns.cf.dns.records.update')
def test_integration(mock_update, mock_list):
    # Mock the list response
    mock_list.return_value.to_json.return_value = '{"result": [{"id": "record_id", "name": "example.com", "content": "1.2.3.4"}]}'
    os.environ['CLOUDFLARE_ZONE_ID'] = 'zone_id'
    os.environ['CLOUDFLARE_IP_ADDRESSES'] = '1.1.1.1,2.2.2.2,3.3.3.3'
    
    records = fetch_records()
    assert len(records['result']) == 1
    assert records['result'][0]['id'] == 'record_id'
    assert records['result'][0]['name'] == 'example.com'
    assert records['result'][0]['content'] == '1.2.3.4'
    
    new_content = ip_rotation(records['result'][0]['content'])
    update_record(records['result'][0]['id'], new_content, records['result'][0]['type'], records['result'][0]['name'])
    mock_update.assert_called_with(
        dns_record_id='record_id',
        zone_id='zone_id',
        type='A',
        name='example.com',
        content='2.2.2.2',
        id='record_id',
    )


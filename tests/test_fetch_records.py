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

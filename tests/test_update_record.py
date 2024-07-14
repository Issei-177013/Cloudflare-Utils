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

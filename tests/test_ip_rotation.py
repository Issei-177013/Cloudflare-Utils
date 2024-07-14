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
from change_dns import ip_rotation

def test_ip_rotation():
    with patch.dict('os.environ', {'CLOUDFLARE_IP_ADDRESSES': '1.1.1.1,2.2.2.2,3.3.3.3'}):
        assert ip_rotation('1.1.1.1') == '2.2.2.2'
        assert ip_rotation('2.2.2.2') == '3.3.3.3'
        assert ip_rotation('3.3.3.3') == '1.1.1.1'
        assert ip_rotation('4.4.4.4') == '1.1.1.1'

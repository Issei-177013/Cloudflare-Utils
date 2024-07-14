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
import json
from cloudflare import Cloudflare, APIError

# Load environment variables from .bashrc
bashrc_path = os.path.expanduser('~/.bashrc')
if os.path.exists(bashrc_path):
    with open(bashrc_path) as f:
        for line in f:
            if line.startswith('export '):
                var, value = line.replace('export ', '', 1).strip().split('=', 1)
                os.environ[var] = value.strip('"')

# Fetch the environment variables
api_token = os.getenv('CLOUDFLARE_API_TOKEN')
zone_id = os.getenv('CLOUDFLARE_ZONE_ID')
record_name = os.getenv('CLOUDFLARE_RECORD_NAME')
ip_addresses = os.getenv('CLOUDFLARE_IP_ADDRESSES')

if not api_token or not zone_id or not record_name or not ip_addresses:
    raise ValueError("CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID, CLOUDFLARE_RECORD_NAME and CLOUDFLARE_IP_ADDRESSES must be set")

# Convert the comma-separated string of IP addresses to a list
ip_addresses = ip_addresses.split(',')

# Initialize Cloudflare client
cf = Cloudflare(api_token=api_token)

def fetch_records():
    try:
        dns_records = cf.dns.records.list(zone_id=zone_id).to_json()
        return json.loads(dns_records)
    except APIError as e:
        print(f"Fetching error: {e}")
        return None

def update_record(record_id, new_content, record_type, record_name):
    try:
        cf.dns.records.update(
            dns_record_id=record_id,
            zone_id=zone_id,
            type=record_type,
            name=record_name,
            content=new_content,
            id=record_id,
        )
    except APIError as e:
        print(f"Updating error: {e}")

def ip_rotation(current_ip):
    try:
        current_index = ip_addresses.index(current_ip)
    except ValueError:
        current_index = -1
    next_index = (current_index + 1) % len(ip_addresses)
    next_ip = ip_addresses[next_index]
    return next_ip

records = fetch_records()

if records:
    for record in records['result']:
        if record['name'] == record_name:
            content = record['content']
            record_id = record['id']
            record_type = record['type']
            new_content = ip_rotation(content)
            update_record(record_id, new_content, record_type, record_name)
else:
    print("No records found")

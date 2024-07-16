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
from tabulate import tabulate

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

if not api_token or not zone_id:
    raise ValueError("show_dns: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID must be set")

# Initialize Cloudflare client
cf = Cloudflare(api_token=api_token)

def fetch_records():
    try:
        dns_records = cf.dns.records.list(zone_id=zone_id).to_json()
        return json.loads(dns_records)
    except APIError as e:
        print(f"Fetching error: {e}")
        return None
    
records = fetch_records()

# Prepare data for tabulate
table_data = []
for index, record in enumerate(records['result'], start=1):
    table_data.append([
        index,
        record['name'],
        record['type'],
        record['content'],
        record.get('comment', 'N/A'),
    ])

# Define headers for the table
headers = ["#", "Name", "Type", "Content", "Comment"]

# Print the table using tabulate
print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", numalign="center"))


# try:
#     row_index = int(input("Enter the index of the row to get its content (or 0 to exit): "))
    
#     if 1 <= row_index <= len(records['result']):
#         selected_record = records['result'][row_index - 1]
#         print(f"Content of the selected row ({row_index}): {selected_record['content']}")
#     elif row_index == 0:
#         print("Exiting...")
#     else:
#         print("Invalid row index. Please enter a valid index.")
# except ValueError:
#     print("Invalid input. Please enter a valid number.")
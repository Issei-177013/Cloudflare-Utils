import os
import json
from cloudflare import Cloudflare, APIError

# os.environ['CLOUDFLARE_API_TOKEN'] = 'qygRTTjNOELiofGToh5xsr9vsKZqWWRaWMA2afQL'
# os.environ['CLOUDFLARE_ZONE_ID'] = 'dac991aa3c4aacb5ea5c80eae3e1afba'
# os.environ['CLOUDFLARE_RECORD_NAME'] = 'tv.niannian.ir'
# os.environ['CLOUDFLARE_IP_ADDRESSES'] = '193.39.9.26,185.218.139.30'

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

import os
from dotenv import load_dotenv
from cloudflare import Cloudflare, APIError
from version import __version__

print(f"🔁 Running Cloudflare-Utils {__version__}")

# Load .env
dotenv_path = '/opt/Cloudflare-Utils/.env'
load_dotenv(dotenv_path)

# Get vars
api_token = os.getenv('CLOUDFLARE_API_TOKEN')
zone_id = os.getenv('CLOUDFLARE_ZONE_ID')
record_name = os.getenv('CLOUDFLARE_RECORD_NAME')
ip_addresses = os.getenv('CLOUDFLARE_IP_ADDRESSES')

if not all([api_token, zone_id, record_name, ip_addresses]):
    raise ValueError("Required environment variables are missing.")

ip_addresses = ip_addresses.split(',')

# Cloudflare client
cf = Cloudflare(api_token=api_token)

# Fetch records
def fetch_records():
    try:
        return cf.dns.records.list(zone_id=zone_id)
    except APIError as e:
        print(f"❌ Fetching error: {e}")
        return []

# Update record
def update_record(record_id, new_content, record_type, record_name, proxied=False):
    try:
        cf.dns.records.update(
            zone_id=zone_id,
            dns_record_id=record_id,
            name=record_name,
            type=record_type,
            content=new_content,
            proxied=proxied
        )
        print(f"✅ DNS record updated to {new_content}")
    except APIError as e:
        print(f"❌ Updating error: {e}")

# Rotate IP
def ip_rotation(current_ip):
    if current_ip not in ip_addresses:
        print(f"ℹ️ Current IP '{current_ip}' not in list. Rotating to first.")
        return ip_addresses[0]
    idx = ip_addresses.index(current_ip)
    return ip_addresses[(idx + 1) % len(ip_addresses)]

# Main
records = fetch_records()

if records:
    for record in records:
        if record.name == record_name:
            old_ip = record.content
            new_ip = ip_rotation(old_ip)
            update_record(record.id, new_ip, record.type, record.name, getattr(record, "proxied", False))
else:
    print("❌ No records found.")
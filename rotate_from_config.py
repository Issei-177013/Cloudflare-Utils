from config_manager import load_config
from cloudflare import Cloudflare, APIError
import json
import os
import time

ROTATION_STATUS_PATH = "rotation_status.json"
DEFAULT_ROTATION_INTERVAL_MINUTES = 30

def load_rotation_status():
    if not os.path.exists(ROTATION_STATUS_PATH):
        return {}
    with open(ROTATION_STATUS_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {} # Return empty dict if file is corrupted or empty

def save_rotation_status(status_data):
    with open(ROTATION_STATUS_PATH, "w") as f:
        json.dump(status_data, f, indent=2)

def rotate_ip(ip_list, current_ip):
    if current_ip not in ip_list:
        return ip_list[0]
    idx = ip_list.index(current_ip)
    return ip_list[(idx + 1) % len(ip_list)]

def run_rotation():
    config = load_config()
    rotation_status = load_rotation_status()
    current_time_seconds = time.time()

    for account in config["accounts"]:
        cf = Cloudflare(api_token=account["api_token"])
        for zone in account.get("zones", []):
            zone_id = zone["zone_id"]
            try:
                records_from_cf = cf.dns.records.list(zone_id=zone_id)
            except APIError as e:
                print(f"❌ Zone fetch error: {zone['domain']}: {e}")
                continue

            for cfg_record in zone.get("records", []):
                record_name = cfg_record["name"]
                record_key = f"{zone_id}_{record_name}" # Unique key for status tracking

                # Determine rotation interval
                custom_interval_minutes = cfg_record.get("rotation_interval_minutes")
                rotation_interval_minutes = custom_interval_minutes if custom_interval_minutes is not None else DEFAULT_ROTATION_INTERVAL_MINUTES
                rotation_interval_seconds = rotation_interval_minutes * 60

                # Check if rotation is due
                last_rotated_at_seconds = rotation_status.get(record_key, 0) # Defaults to 0 if never rotated
                if current_time_seconds - last_rotated_at_seconds < rotation_interval_seconds:
                    print(f"ℹ️ Rotation for {record_name} not due yet. Last rotated { (current_time_seconds - last_rotated_at_seconds) / 60:.1f} minutes ago. Interval: {rotation_interval_minutes} min.")
                    continue
                
                matching_cf_record = next((r for r in records_from_cf if r.name == record_name), None)
                if not matching_cf_record:
                    print(f"⚠️ Record not found in Cloudflare: {record_name}")
                    continue

                current_ip_on_cf = matching_cf_record.content
                new_ip = rotate_ip(cfg_record["ips"], current_ip_on_cf)
                
                if new_ip == current_ip_on_cf:
                    print(f"ℹ️ IP for {record_name} is already {new_ip}. No update needed, but resetting rotation timer as per schedule.")
                    rotation_status[record_key] = current_time_seconds
                    save_rotation_status(rotation_status)
                    continue

                try:
                    cf.dns.records.update(
                        zone_id=zone_id,
                        dns_record_id=matching_cf_record.id,
                        name=record_name,
                        type=cfg_record["type"],
                        content=new_ip,
                        proxied=cfg_record.get("proxied", False)
                    )
                    print(f"✅ Updated {record_name} to {new_ip}")
                    rotation_status[record_key] = current_time_seconds # Update last rotation time
                except APIError as e:
                    print(f"❌ Update error for {record_name}: {e}")
    
    save_rotation_status(rotation_status)

if __name__ == "__main__":
    run_rotation()

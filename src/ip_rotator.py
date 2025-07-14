import time
import logging
from .config import load_config, load_rotation_status, save_rotation_status, DEFAULT_ROTATION_INTERVAL_MINUTES
from .cloudflare_api import CloudflareAPI
from cloudflare import APIError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def rotate_ip(ip_list, current_ip):
    if current_ip not in ip_list:
        return ip_list[0]
    if not ip_list:
        logging.warning("IP list is empty. Cannot rotate.")
        return current_ip

    if current_ip not in ip_list:
        return ip_list[0]

    if len(ip_list) == 1:
        return ip_list[0]

    current_idx = ip_list.index(current_ip)
    next_idx = (current_idx + 1) % len(ip_list)
    new_ip = ip_list[next_idx]

    if new_ip == current_ip and len(set(ip_list)) > 1:
        logging.info(f"Initial rotation choice for {current_ip} resulted in the same IP ({new_ip}). Trying to find a different one.")
        next_idx = (next_idx + 1) % len(ip_list)
        new_ip = ip_list[next_idx]

    return new_ip

def run_rotation():
    config = load_config()
    rotation_status = load_rotation_status()
    current_time_seconds = time.time()

    for account in config["accounts"]:
        cf_api = CloudflareAPI(account["api_token"])
        for zone in account.get("zones", []):
            zone_id = zone["zone_id"]
            try:
                records_from_cf = cf_api.list_dns_records(zone_id)
            except APIError as e:
                logging.error(f"Zone fetch error: {zone['domain']}: {e}")
                continue

            for cfg_record in zone.get("records", []):
                record_name = cfg_record["name"]
                record_key = f"{zone_id}_{record_name}"

                custom_interval_minutes = cfg_record.get("rotation_interval_minutes")
                rotation_interval_minutes = custom_interval_minutes if custom_interval_minutes is not None else DEFAULT_ROTATION_INTERVAL_MINUTES
                rotation_interval_seconds = rotation_interval_minutes * 60

                last_rotated_at_seconds = rotation_status.get(record_key, 0)
                if current_time_seconds - last_rotated_at_seconds < rotation_interval_seconds:
                    logging.info(f"Rotation for {record_name} not due yet. Last rotated { (current_time_seconds - last_rotated_at_seconds) / 60:.1f} minutes ago. Interval: {rotation_interval_minutes} min.")
                    continue
                
                matching_cf_record = next((r for r in records_from_cf if r.name == record_name), None)
                if not matching_cf_record:
                    logging.warning(f"Record not found in Cloudflare: {record_name}")
                    continue

                current_ip_on_cf = matching_cf_record.content
                new_ip = rotate_ip(cfg_record["ips"], current_ip_on_cf)
                
                if new_ip == current_ip_on_cf:
                    logging.info(f"IP for {record_name} is already {new_ip}. No update needed, but resetting rotation timer as per schedule.")
                    rotation_status[record_key] = current_time_seconds
                    save_rotation_status(rotation_status)
                    continue

                try:
                    cf_api.update_dns_record(
                        zone_id=zone_id,
                        dns_record_id=matching_cf_record.id,
                        name=record_name,
                        type=cfg_record["type"],
                        content=new_ip
                    )
                    logging.info(f"Updated {record_name} to {new_ip}")
                    rotation_status[record_key] = current_time_seconds
                except APIError as e:
                    logging.error(f"Update error for {record_name}: {e}")
    
    save_rotation_status(rotation_status)

if __name__ == "__main__":
    run_rotation()
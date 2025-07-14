import logging
from .config import load_config, save_config, find_account, find_zone, find_record

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def add_record(account_name, zone_domain, record_name, record_type, ips, proxied, rotation_interval_minutes):
    data = load_config()
    acc = find_account(data, account_name)
    if not acc:
        logging.error(f"Account '{account_name}' not found.")
        return

    zone = find_zone(acc, zone_domain)
    if not zone:
        logging.error(f"Zone '{zone_domain}' not found in account '{account_name}'.")
        return

    if find_record(zone, record_name):
        logging.warning(f"Record '{record_name}' already exists in zone '{zone_domain}'.")
        print(f"❌ Record '{record_name}' already exists in zone '{zone_domain}'.")
        return

    record_data = {
        "name": record_name,
        "type": record_type,
        "ips": ips,
        "proxied": proxied,
    }
    if rotation_interval_minutes is not None:
        record_data["rotation_interval_minutes"] = rotation_interval_minutes

    zone["records"].append(record_data)
    save_config(data)
    logging.info(f"Record '{record_name}' added to zone '{zone_domain}'.")
    print("✅ Record added successfully!")

def delete_record(account_name, zone_domain, record_name):
    data = load_config()
    acc = find_account(data, account_name)
    if not acc:
        logging.error(f"Account '{account_name}' not found.")
        return

    zone = find_zone(acc, zone_domain)
    if not zone:
        logging.error(f"Zone '{zone_domain}' not found in account '{account_name}'.")
        return

    record_to_delete = find_record(zone, record_name)
    if not record_to_delete:
        logging.warning(f"Record '{record_name}' not found in zone '{zone_domain}'.")
        print(f"❌ Record '{record_name}' not found in zone '{zone_domain}'.")
        return

    zone["records"].remove(record_to_delete)
    save_config(data)
    logging.info(f"Record '{record_to_delete['name']}' deleted successfully from local configuration.")
    print(f"✅ Record '{record_to_delete['name']}' deleted successfully from local configuration.")


def edit_record(account_name, zone_domain, record_name, new_ips, new_type, new_proxied, new_interval):
    data = load_config()
    acc = find_account(data, account_name)
    if not acc:
        logging.error(f"Account '{account_name}' not found.")
        return

    zone = find_zone(acc, zone_domain)
    if not zone:
        logging.error(f"Zone '{zone_domain}' not found in account '{account_name}'.")
        return

    record_to_edit = find_record(zone, record_name)
    if not record_to_edit:
        logging.warning(f"Record '{record_name}' not found in zone '{zone_domain}'.")
        print(f"❌ Record '{record_name}' not found in zone '{zone_domain}'.")
        return

    if new_ips:
        record_to_edit['ips'] = new_ips
    if new_type:
        record_to_edit['type'] = new_type
    if new_proxied is not None:
        record_to_edit['proxied'] = new_proxied
    if new_interval is not None:
        if new_interval.lower() == 'none':
            if 'rotation_interval_minutes' in record_to_edit:
                del record_to_edit['rotation_interval_minutes']
        else:
            try:
                interval = int(new_interval)
                if interval < 5:
                    logging.error("Rotation interval must be at least 5 minutes. Value not changed.")
                else:
                    record_to_edit['rotation_interval_minutes'] = interval
            except ValueError:
                logging.error("Invalid input for interval. Must be a number or 'none'. Value not changed.")

    save_config(data)
    logging.info(f"Record '{record_to_edit['name']}' updated successfully.")
    print(f"✅ Record '{record_to_edit['name']}' updated successfully.")

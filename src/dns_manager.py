from .config import load_config, validate_and_save_config, find_account, find_zone, find_record
from .validator import is_valid_record_type
from .logger import dns_manager_logger

def add_record(account_name, zone_domain, record_name, record_type, ips, rotation_interval_minutes):
    if not is_valid_record_type(record_type):
        dns_manager_logger.error(f"Invalid record type: {record_type}")
        print(f"❌ Invalid record type '{record_type}'. Must be 'A' or 'AAAA'.")
        return
    data = load_config()
    acc = find_account(data, account_name)
    if not acc:
        dns_manager_logger.error(f"Account '{account_name}' not found.")
        return

    zone = find_zone(acc, zone_domain)
    if not zone:
        dns_manager_logger.error(f"Zone '{zone_domain}' not found in account '{account_name}'.")
        return

    if find_record(zone, record_name):
        dns_manager_logger.warning(f"Record '{record_name}' already exists in zone '{zone_domain}'.")
        print(f"❌ Record '{record_name}' already exists in zone '{zone_domain}'.")
        return

    record_data = {
        "name": record_name,
        "type": record_type,
        "ips": ips,
    }
    if rotation_interval_minutes is not None:
        record_data["rotation_interval_minutes"] = rotation_interval_minutes

    zone["records"].append(record_data)
    if validate_and_save_config(data):
        dns_manager_logger.info(f"Record '{record_name}' added to zone '{zone_domain}'.")
        print("✅ Record added successfully!")

def delete_record(account_name, zone_domain, record_name):
    data = load_config()
    acc = find_account(data, account_name)
    if not acc:
        dns_manager_logger.error(f"Account '{account_name}' not found.")
        return

    zone = find_zone(acc, zone_domain)
    if not zone:
        dns_manager_logger.error(f"Zone '{zone_domain}' not found in account '{account_name}'.")
        return

    record_to_delete = find_record(zone, record_name)
    if not record_to_delete:
        dns_manager_logger.warning(f"Record '{record_name}' not found in zone '{zone_domain}'.")
        print(f"❌ Record '{record_name}' not found in zone '{zone_domain}'.")
        return

    zone["records"].remove(record_to_delete)
    if validate_and_save_config(data):
        dns_manager_logger.info(f"Record '{record_to_delete['name']}' deleted successfully from local configuration.")
        print(f"✅ Record '{record_to_delete['name']}' deleted successfully from local configuration.")


def edit_record(account_name, zone_domain, record_name, new_ips, new_type, new_interval):
    data = load_config()
    acc = find_account(data, account_name)
    if not acc:
        dns_manager_logger.error(f"Account '{account_name}' not found.")
        return

    zone = find_zone(acc, zone_domain)
    if not zone:
        dns_manager_logger.error(f"Zone '{zone_domain}' not found in account '{account_name}'.")
        return

    record_to_edit = find_record(zone, record_name)
    if not record_to_edit:
        dns_manager_logger.warning(f"Record '{record_name}' not found in zone '{zone_domain}'.")
        print(f"❌ Record '{record_name}' not found in zone '{zone_domain}'.")
        return

    if new_ips:
        record_to_edit['ips'] = new_ips
    if new_type:
        if is_valid_record_type(new_type):
            record_to_edit['type'] = new_type
        else:
            dns_manager_logger.error(f"Invalid record type provided for edit: {new_type}")
            print(f"❌ Invalid record type '{new_type}'. Value not changed.")
            
    if new_interval is not None:
        if new_interval.lower() == 'none':
            if 'rotation_interval_minutes' in record_to_edit:
                del record_to_edit['rotation_interval_minutes']
        else:
            try:
                interval = int(new_interval)
                if interval < 5:
                    dns_manager_logger.error("Rotation interval must be at least 5 minutes. Value not changed.")
                else:
                    record_to_edit['rotation_interval_minutes'] = interval
            except ValueError:
                dns_manager_logger.error("Invalid input for interval. Must be a number or 'none'. Value not changed.")

    if validate_and_save_config(data):
        dns_manager_logger.info(f"Record '{record_to_edit['name']}' updated successfully.")
        print(f"✅ Record '{record_to_edit['name']}' updated successfully.")

def edit_account_in_config(account_name, new_name, new_token):
    data = load_config()
    acc = find_account(data, account_name)
    if not acc:
        dns_manager_logger.error(f"Account '{account_name}' not found.")
        return

    if new_name:
        acc['name'] = new_name
    if new_token:
        acc['api_token'] = new_token

    if validate_and_save_config(data):
        dns_manager_logger.info(f"Account '{account_name}' updated successfully.")
        print(f"✅ Account '{account_name}' updated successfully.")

def delete_account_from_config(account_name):
    data = load_config()
    acc = find_account(data, account_name)
    if not acc:
        dns_manager_logger.error(f"Account '{account_name}' not found.")
        return

    data['accounts'].remove(acc)
    if validate_and_save_config(data):
        dns_manager_logger.info(f"Account '{account_name}' deleted successfully.")
        print(f"✅ Account '{account_name}' deleted successfully.")

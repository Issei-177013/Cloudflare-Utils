from cloudflare import Cloudflare, APIError
import json
import os
import time
import sys # Added for sys.exit

# Determine the absolute path to the directory where this script (config_manager.py) is located.
# This ensures that configs.json and rotation_status.json are found relative to the script's location,
# which is crucial if the script is called from a different working directory (e.g., when installed as cfutils).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "configs.json")
ROTATION_STATUS_PATH = os.path.join(SCRIPT_DIR, "rotation_status.json")

DEFAULT_ROTATION_INTERVAL_MINUTES = 30

def load_config():
    """Loads the configuration from the JSON file."""
    if not os.path.exists(CONFIG_PATH):
        # If the config file doesn't exist, create it with default structure
        print(f"Info: Config file not found at {CONFIG_PATH}. Creating a new one.")
        new_config = {"accounts": [], "rotations": []}
        save_config(new_config) # Save default structure
        return new_config
    try:
        with open(CONFIG_PATH, "r") as f:
            config_data = json.load(f)
            if "accounts" not in config_data: # Ensure accounts key exists
                config_data["accounts"] = []
            if "rotations" not in config_data: # Ensure rotations key exists
                config_data["rotations"] = []
            return config_data
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {CONFIG_PATH}. Returning default config.")
        # Optionally, handle this more gracefully, e.g., by backing up the broken file.
        return {"accounts": [], "rotations": []} # Default structure on error

def get_zone_id(cf_client, zone_data):
    """Fetches the zone ID and name for a given zone_data using the Cloudflare API."""
    zone_name_to_lookup = zone_data.get("domain") or zone_data.get("name")

    if not zone_name_to_lookup:
        # This case should ideally be caught before calling get_zone_id,
        # but as a safeguard:
        print(f"Warning: Zone data for account '{zone_data.get('_account_name', 'Unknown Account')}' is missing both 'domain' and 'name' fields. Cannot fetch zone_id.")
        return None, None

    try:
        zones = cf_client.zones.get(params={'name': zone_name_to_lookup})
        if zones:
            # Assuming the first match is the correct one
            return zones[0].id, zones[0].name
        else:
            print(f"Warning: Zone '{zone_name_to_lookup}' not found on Cloudflare account.")
            return None, None
    except APIError as e:
        print(f"Error: API error while fetching zone ID for '{zone_name_to_lookup}': {e}")
        return None, None
    except Exception as e: # Catch any other unexpected errors
        print(f"Error: An unexpected error occurred while fetching zone ID for '{zone_name_to_lookup}': {e}")
        return None, None

def load_config():
    """Loads the configuration from the JSON file."""
    if not os.path.exists(CONFIG_PATH):
        # If the config file doesn't exist, create it with default structure
        print(f"Info: Config file not found at {CONFIG_PATH}. Creating a new one.")
        new_config = {"accounts": [], "rotations": []}
        save_config(new_config) # Save default structure
        return new_config
    try:
        with open(CONFIG_PATH, "r") as f:
            config_data = json.load(f)
            if "accounts" not in config_data: # Ensure accounts key exists
                config_data["accounts"] = []
            if "rotations" not in config_data: # Ensure rotations key exists
                config_data["rotations"] = []

            # Iterate through accounts and zones to fetch missing zone_ids
            for account in config_data.get("accounts", []):
                if "api_token" not in account:
                    print(f"Warning: Account '{account.get('name', 'Unnamed Account')}' is missing API token. Skipping zone ID fetches for this account.")
                    continue

                cf_client = Cloudflare(api_token=account["api_token"])
                valid_zones = []
                account_name_for_logging = account.get('name', 'Unnamed Account')
                for zone in account.get("zones", []):
                    # Add account name to zone data for logging purposes in get_zone_id, if needed
                    zone['_account_name'] = account_name_for_logging

                    if "zone_id" not in zone or not zone["zone_id"]:
                        # Domain might be missing, get_zone_id will try zone.get("name")
                        domain_present_in_config = bool(zone.get("domain"))
                        
                        # Pass the whole zone dictionary
                        zone_id, fetched_zone_name = get_zone_id(cf_client, zone) 

                        if zone_id:
                            zone["zone_id"] = zone_id
                            print(f"Info: Successfully fetched 'zone_id' for '{fetched_zone_name}': {zone_id}")
                            if not domain_present_in_config and fetched_zone_name:
                                zone["domain"] = fetched_zone_name
                                print(f"Info: Populated 'domain' field with '{fetched_zone_name}' for zone in account '{account_name_for_logging}'.")
                            valid_zones.append(zone)
                        else:
                            # get_zone_id already prints warnings/errors
                            print(f"Warning: Could not fetch 'zone_id' for zone initially identified by data: {zone}. This zone will be skipped.")
                    else:
                        # If zone_id is present, ensure domain is also present if possible.
                        # This might be redundant if we assume configs with zone_id always have domain,
                        # but good for robustness.
                        if not zone.get("domain") and zone.get("name"):
                             # This scenario is less likely if zone_id is present, but as a fallback.
                            print(f"Info: Zone '{zone.get('name')}' in account '{account_name_for_logging}' has 'zone_id' but no 'domain'. Attempting to use 'name' as 'domain'.")
                            zone["domain"] = zone["name"]
                        elif not zone.get("domain") and not zone.get("name"):
                            print(f"Warning: Zone in account '{account_name_for_logging}' has 'zone_id' but is missing 'domain' and 'name'. Cannot ensure 'domain' field consistency.")
                        valid_zones.append(zone) # Zone already has a zone_id
                
                # Clean up temporary '_account_name' field from zones before saving
                for z in valid_zones:
                    if '_account_name' in z:
                        del z['_account_name']
                account["zones"] = valid_zones

            return config_data
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {CONFIG_PATH}. Returning default config.")
        return {"accounts": [], "rotations": []} # Default structure on error

def save_config(data):
    """Saves the configuration data to the JSON file."""
    # Ensure both keys exist before saving, even if empty
    if "accounts" not in data:
        data["accounts"] = []
    if "rotations" not in data:
        data["rotations"] = []
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

def find_account(data, account_name):
    """Finds an account by name in the config data."""
    for acc in data.get("accounts", []):
        if acc.get("name") == account_name:
            return acc
    return None

def find_zone(account_data, zone_domain):
    """Finds a zone by domain within an account's data."""
    for zone in account_data.get("zones", []):
        if zone.get("domain") == zone_domain:
            return zone
    return None

def find_record(zone_data, record_name):
    """Finds a record by name within a zone's data."""
    for record in zone_data.get("records", []):
        if record.get("name") == record_name:
            return record
    return None

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
    if not ip_list:
        # This case should ideally be prevented by validation elsewhere,
        # but as a safeguard:
        print("⚠️ Warning: IP list is empty. Cannot rotate.")
        return current_ip # Or None, depending on desired behavior for empty list

    if current_ip not in ip_list:
        # If current IP in CF is not in our list (e.g., manually changed),
        # or if it's the first time, just pick the first IP from our list.
        return ip_list[0]

    if len(ip_list) == 1:
        # Only one IP in the list, so it will always be this one.
        return ip_list[0]

    current_idx = ip_list.index(current_ip)
    next_idx = (current_idx + 1) % len(ip_list)
    new_ip = ip_list[next_idx]

    # If the initially selected new_ip is the same as the current_ip,
    # and there are other distinct IPs available in the list, try to advance once more.
    if new_ip == current_ip and len(set(ip_list)) > 1:
        print(f"ℹ️ Initial rotation choice for {current_ip} resulted in the same IP ({new_ip}). Trying to find a different one.")
        next_idx = (next_idx + 1) % len(ip_list)
        new_ip = ip_list[next_idx]
        # If it's *still* the same IP after advancing again, it means all IPs in the list are effectively the same
        # or we've cycled through all unique IPs and landed back where we started with current_ip.
        # Example: ips = ["1.1.1.1", "2.2.2.2"], current_ip = "1.1.1.1".
        # 1. new_ip becomes "2.2.2.2". Condition (new_ip == current_ip) is false. Returns "2.2.2.2".
        # Example: ips = ["1.1.1.1", "1.1.1.1", "2.2.2.2"], current_ip = "1.1.1.1" (first one)
        # 1. current_idx = 0. next_idx = 1. new_ip = "1.1.1.1" (second one).
        # 2. (new_ip == current_ip) is true. len(set(ip_list)) is 2 (>1).
        # 3. next_idx becomes (1+1)%3 = 2. new_ip becomes "2.2.2.2".
        # 4. Returns "2.2.2.2". This seems correct.

        # Example: ips = ["1.1.1.1", "1.1.1.1"], current_ip = "1.1.1.1"
        # 1. current_idx = 0. next_idx = 1. new_ip = "1.1.1.1".
        # 2. (new_ip == current_ip) is true. len(set(ip_list)) is 1 (not >1).
        # 3. Condition is false. Returns "1.1.1.1". This is correct.

    return new_ip

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
    try:
        run_rotation()
    except KeyboardInterrupt:
        print("\n🛑 IP rotation process interrupted by user. Exiting gracefully.")
        # Potentially save any partially updated rotation_status here if needed,
        # but current save_rotation_status is called after each successful update or at the very end.
        # If interrupted mid-API call, the status file wouldn't have been updated for that specific record yet.
        # If interrupted during save_rotation_status itself, the file might be corrupted.
        # For simplicity, we'll rely on the atomicity of file writes or accept potential minor inconsistency
        # in rotation_status if interrupted at the exact moment of saving.
        # A more robust solution might involve temporary files and atomic renames for saving status.
        # However, the prompt asks for graceful exit to prevent traceback, which this achieves.
        try:
            sys.exit(0) # Importing sys for this
        except SystemExit:
            os._exit(0) # Importing os for this

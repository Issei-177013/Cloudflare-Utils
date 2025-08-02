import os
import sys
import subprocess
from .config import load_config, validate_and_save_config, find_account, find_zone, find_record, CONFIG_PATH, find_rotation_group
from .cloudflare_api import CloudflareAPI
from .dns_manager import add_record as add_record_to_config, delete_record as delete_record_from_config, edit_record as edit_record_in_config, edit_account_in_config, delete_account_from_config, add_rotation_group, edit_rotation_group, delete_rotation_group
from .ip_rotator import rotate_ips_between_records, rotate_ips_for_multi_record
from .state_manager import load_state, save_state
from .input_helper import get_validated_input, get_ip_list, get_record_type, get_rotation_interval
from .validator import is_valid_domain, is_valid_zone_id, is_valid_record_name
from .logger import logger, LOGS_DIR
from .display import display_as_table, summarize_list
from cloudflare import APIError

def clear_screen():
    """Clears the terminal screen."""
    # For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # For macOS and Linux
    else:
        _ = os.system('clear')

def ensure_root():
    """Ensures the script is running as root, elevating with sudo if necessary."""
    if os.geteuid() != 0:
        logger.warning("Not running as root. Attempting to elevate privileges with sudo.")
        print("This script must be run as root. Attempting to elevate privileges...")
        try:
            # Relaunch the script with sudo
            subprocess.check_call(['sudo', sys.executable] + sys.argv)
            # Exit the original non-elevated process
            sys.exit(0)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to elevate privileges using sudo: {e}")
            print(f"\nFailed to gain root access. Please run the command with 'sudo'.")
            sys.exit(1)
        except FileNotFoundError:
            logger.error("`sudo` command not found.")
            print("\n`sudo` is required to elevate privileges but was not found.")
            print("Please run this script as root.")
            sys.exit(1)

def select_from_list(items, prompt):
    """Displays a numbered list of items and returns the selected item."""
    if not items:
        print("No items to select.")
        return None

    print(prompt)
    for i, item in enumerate(items):
        # Assuming item is a dictionary and has a 'name' or 'domain' key
        name = item.get('name', item.get('domain', 'Unknown Item'))
        print(f"{i+1}. {name}")

    while True:
        try:
            choice = int(input("Enter your choice (number): "))
            if 1 <= choice <= len(items):
                return items[choice-1]
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def add_account():
    data = load_config()
    name = get_validated_input("Account name: ", lambda s: s.strip(), "Account name cannot be empty.")

    if find_account(data, name):
        logger.warning("Account already exists")
        print("❌ Account already exists")
        return

    print("ℹ️ INFO: While a Global API Key will work, it's STRONGLY recommended to use a specific API Token.")
    print("Create one at: https://dash.cloudflare.com/profile/api-tokens (My Profile > API Tokens > Create Token).")
    print("This provides better security and scoped permissions.")

    while True:
        token = get_validated_input("Cloudflare API Token: ", lambda s: s.strip(), "API Token cannot be empty.")
        try:
            print("🔐 Verifying token...")
            cf_api = CloudflareAPI(token)
            cf_api.verify_token()  # This will attempt to list zones
            print("✅ Token is valid.")
            break  # Exit loop if token is valid
        except APIError as e:
            logger.error(f"Cloudflare API Error on token verification: {e}")
            print(f"❌ Invalid Token. Cloudflare API Error: {e}")
            if not confirm_action("Try again?"):
                logger.warning("User aborted account creation.")
                return

    data["accounts"].append({"name": name, "api_token": token, "zones": []})
    if validate_and_save_config(data):
        logger.info(f"Account '{name}' added.")
        print("✅ Account added")

def edit_account():
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to edit:")
    if not acc:
        return

    print(f"\n--- Editing Account: {acc['name']} ---")
    new_name = get_validated_input(f"Enter new name (or press Enter to keep '{acc['name']}'): ", lambda s: s.strip(), allow_empty=True)
    new_token = get_validated_input("Enter new API token (or press Enter to keep current): ", lambda s: s.strip(), allow_empty=True)

    if new_name or new_token:
        edit_account_in_config(acc['name'], new_name, new_token)
    else:
        print("No changes made.")

def delete_account():
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to delete:")
    if not acc:
        return

    if confirm_action(f"Are you sure you want to delete the account '{acc['name']}'?"):
        delete_account_from_config(acc['name'])
        logger.info(f"Account '{acc['name']}' deleted.")
    else:
        logger.info("Deletion cancelled.")

def add_record():
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
        print("❌ No accounts available. Please add an account first.")
        return

    acc = select_from_list(data["accounts"], "Select an account:")
    if not acc:
        return

    try:
        cf_api = CloudflareAPI(acc["api_token"])
        zones_from_cf = cf_api.list_zones()
        
        # Convert the generator to a list of dictionaries for selection
        zones_for_selection = [{"id": zone.id, "name": zone.name} for zone in zones_from_cf]

        if not zones_for_selection:
            logger.warning(f"No zones found for account '{acc['name']}' in Cloudflare.")
            print("❌ No zones available in this account. Please add a zone in your Cloudflare account first.")
            return

        selected_zone_info = select_from_list(zones_for_selection, "Select a zone from Cloudflare:")
        if not selected_zone_info:
            return

        # Check if the zone is already in the local config, if not, add it.
        zone_domain = selected_zone_info['name']
        zone_id = selected_zone_info['id']
        zone = find_zone(acc, zone_domain)
        if not zone:
            if "zones" not in acc:
                acc["zones"] = []
            zone = {"domain": zone_domain, "zone_id": zone_id, "records": []}
            acc["zones"].append(zone)
            validate_and_save_config(data)
            logger.info(f"Zone '{zone_domain}' added to local config.")
        else:
            logger.info(f"Zone '{zone_domain}' already exists in local config.")

    except APIError as e:
        logger.error(f"Cloudflare API Error fetching zones: {e}")
        print("❌ Could not fetch zones from Cloudflare.")
        return

    record_name = None
    try:
        cf_api = CloudflareAPI(acc["api_token"])
        zone_id = zone["zone_id"]
        logger.info(f"Fetching records for zone {zone['domain']}...")
        records_from_cf = list(cf_api.list_dns_records(zone_id))
        
        if records_from_cf:
            print("\n--- Existing Records ---")
            for i, cf_record in enumerate(records_from_cf):
                print(f"{i+1}. {cf_record.name} (Type: {cf_record.type}, Content: {cf_record.content})")
            print(f"{len(records_from_cf)+1}. Enter a new record name manually")
            print("-------------------------")
            
            while True:
                try:
                    choice = int(input("👉 Select a record to use/update or choose manual entry: "))
                    if 1 <= choice <= len(records_from_cf):
                        record_name = records_from_cf[choice-1].name
                        logger.info(f"Using existing record: {record_name}")
                        break
                    elif choice == len(records_from_cf) + 1:
                        logger.info("Manual record name entry selected.")
                        break
                    else:
                        print("❌ Invalid choice.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
        else:
            logger.info(f"No existing records found in Cloudflare for zone {zone['domain']}. Proceeding with manual entry.")

    except APIError as e:
        logger.error(f"Cloudflare API Error fetching records: {e}")
        print("⚠️ Proceeding with manual record name entry.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print("⚠️ Proceeding with manual record name entry.")

    if not record_name:
        record_name = get_validated_input(
            "Record name (e.g., vpn.example.com): ",
            is_valid_record_name,
            "Invalid record name."
        )

    if find_record(zone, record_name):
        logger.warning(f"Record '{record_name}' already exists locally.")
        print("ℹ️ To update, please delete and re-add it.")
        return

    rec_type = get_record_type()
    ip_list = get_ip_list(rec_type)
    rotation_interval_minutes = get_rotation_interval()

    add_record_to_config(acc['name'], zone['domain'], record_name, rec_type, ip_list, rotation_interval_minutes)
    logger.info(f"Record '{record_name}' added to zone '{zone['domain']}'.")

def list_records_from_config():
    data = load_config()
    if not any(acc.get("zones") for acc in data["accounts"]):
        logger.info("No records to display.")
        print("No records configured for rotation. Please add a record first.")
        return

    print("\n--- Records Configured for Rotation ---")
    
    all_records_data = []
    for acc in data["accounts"]:
        for zone in acc.get("zones", []):
            for record in zone.get("records", []):
                all_records_data.append({
                    "Account": acc["name"],
                    "Zone": zone["domain"],
                    "Record": record["name"],
                    "Type": record["type"],
                    "IPs": summarize_list(record.get("ips", [])),
                    "Interval (min)": record.get('rotation_interval_minutes', 'Default (30)')
                })

    if all_records_data:
        headers = {
            "Account": "Account",
            "Zone": "Zone",
            "Record": "Record",
            "Type": "Type",
            "IPs": "IPs",
            "Interval (min)": "Interval (min)"
        }
        display_as_table(all_records_data, headers)
    else:
        print("No records configured for rotation.")


def list_all():
    data = load_config()
    if not data["accounts"]:
        logger.info("No accounts to display.")
        print("No accounts configured. Please add an account first.")
        return

    print("\n--- All Accounts, Zones, and Records from Cloudflare ---")
    for acc in data["accounts"]:
        print(f"\n\n--- Account: {acc['name']} ---")
        try:
            cf_api = CloudflareAPI(acc["api_token"])
            zones_from_cf = list(cf_api.list_zones())

            if not zones_from_cf:
                print("No zones found in this Cloudflare account.")
                continue

            zones_data = [{"Name": zone.name, "ID": zone.id} for zone in zones_from_cf]
            print("\nZones:")
            display_as_table(zones_data, headers={"Name": "Name", "ID": "ID"})

            for cf_zone in zones_from_cf:
                print(f"\n--- Records for Zone: {cf_zone.name} ---")
                records_from_cf = list(cf_api.list_dns_records(cf_zone.id))

                if not records_from_cf:
                    print("No DNS records found in this zone.")
                    continue

                records_data = []
                local_zone_config = find_zone(acc, cf_zone.name)
                for cf_record in records_from_cf:
                    rotation_info = "Not Configured"
                    if local_zone_config:
                        local_record_config = find_record(local_zone_config, cf_record.name)
                        if local_record_config:
                            interval = local_record_config.get('rotation_interval_minutes', 'Default (30)')
                            rotation_info = f"Yes ({interval} min)"

                    records_data.append({
                        "Name": cf_record.name,
                        "Type": cf_record.type,
                        "Content": cf_record.content,
                        "Rotation": rotation_info
                    })
                headers = {
                    "Name": "Name",
                    "Type": "Type",
                    "Content": "Content",
                    "Rotation": "Rotation"
                }
                display_as_table(records_data, headers)

        except APIError as e:
            logger.error(f"Cloudflare API Error for account '{acc['name']}': {e}")
            print(f"  ❌ Error fetching data for this account: {e}")
            continue

def delete_record():
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to delete a record from:")
    if not acc:
        return

    if not acc["zones"]:
        logger.warning(f"No zones available in account '{acc['name']}'.")
        print(f"❌ No zones available in account '{acc['name']}'.")
        return

    zone = select_from_list(acc["zones"], f"Select a zone in '{acc['name']}' to delete a record from:")
    if not zone:
        return

    if not zone["records"]:
        logger.warning(f"No records available in zone '{zone['domain']}'.")
        print(f"❌ No records available in zone '{zone['domain']}'.")
        return

    record_to_delete = select_from_list(zone["records"], f"Select a record in '{zone['domain']}' to delete:")
    if not record_to_delete:
        return

    if confirm_action(f"Are you sure you want to delete the record '{record_to_delete['name']}' from zone '{zone['domain']}'?"):
        delete_record_from_config(acc['name'], zone['domain'], record_to_delete['name'])
        logger.info(f"Record '{record_to_delete['name']}' deleted from zone '{zone['domain']}'.")
    else:
        logger.info("Deletion cancelled.")

def edit_record():
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to edit a record in:")
    if not acc:
        return

    if not acc["zones"]:
        logger.warning(f"No zones available in account '{acc['name']}'.")
        print(f"❌ No zones available in account '{acc['name']}'.")
        return

    zone = select_from_list(acc["zones"], f"Select a zone in '{acc['name']}' to edit a record in:")
    if not zone:
        return

    if not zone["records"]:
        logger.warning(f"No records available in zone '{zone['domain']}'.")
        print(f"❌ No records available in zone '{zone['domain']}'.")
        return

    record_to_edit = select_from_list(zone["records"], f"Select a record in '{zone['domain']}' to edit:")
    if not record_to_edit:
        return

    print(f"\n--- Editing Record: {record_to_edit['name']} ---")
    print(f"Current IPs: {', '.join(record_to_edit['ips'])}")
    new_ips_str = input(f"Enter new IPs (comma separated) or press Enter to keep current: ").strip()
    new_ips = [ip.strip() for ip in new_ips_str.split(',')] if new_ips_str else None

    print(f"Current Type: {record_to_edit['type']}")
    new_type = input(f"Enter new type (A/CNAME) or press Enter to keep current: ").strip().upper() or None

    current_interval = record_to_edit.get('rotation_interval_minutes', 'Default (30)')
    print(f"Current Rotation Interval (minutes): {current_interval}")
    new_interval_str = input(f"Enter new interval (minutes, min 5, or 'none' to use default) or press Enter to keep current: ").strip()
    
    edit_record_in_config(acc['name'], zone['domain'], record_to_edit['name'], new_ips, new_type, new_interval_str)
    logger.info(f"Record '{record_to_edit['name']}' in zone '{zone['domain']}' updated.")

def confirm_action(prompt="Are you sure you want to proceed?"):
    """Asks for user confirmation."""
    while True:
        response = input(f"{prompt} (yes/no): ").strip().lower()
        if response in ["yes", "y"]:
            return True
        elif response in ["no", "n"]:
            return False
        else:
            print("❌ Invalid input. Please enter 'yes' or 'no'.")


def rotate_based_on_list_of_ips_single_record_menu():
    """Displays the submenu for rotation based on a list of IPs."""
    while True:
        clear_screen()
        print("\n--- Rotate Based on a List of IPs (Single-Record) ---")
        list_records_from_config() # Always display the list
        print("\n1. 📝 Create DNS Rotation")
        print("2. ✏️ Edit an Existing DNS Rotation")
        print("3. 🗑️ Delete a DNS Rotation")
        print("4. 📄 View logs")
        print("0. ⬅️ Return to previous menu")
        print("------------------------------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            add_record()
        elif choice == "2":
            edit_record()
        elif choice == "3":
            delete_record()
        elif choice == "4":
            data = load_config()
            if not any(acc.get("zones") for acc in data["accounts"]):
                print("No records configured for rotation. Please add a record first.")
                input("\nPress Enter to return...")
                continue
            
            records = []
            for acc in data["accounts"]:
                for zone in acc.get("zones", []):
                    for record in zone.get("records", []):
                        records.append(record)

            if not records:
                print("No records configured for rotation. Please add a record first.")
                input("\nPress Enter to return...")
                continue

            record_to_view = select_from_list(records, "Select a record to view logs for:")
            if record_to_view:
                view_live_logs(record_name=record_to_view['name'])
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print("❌ Invalid choice. Please select a valid option.")


def list_rotation_groups():
    data = load_config()
    groups_data = []
    for acc in data.get("accounts", []):
        for zone in acc.get("zones", []):
            for group in zone.get("rotation_groups", []):
                groups_data.append({
                    "Account": acc["name"],
                    "Zone": zone["domain"],
                    "Group Name": group["name"],
                    "Records": summarize_list(group["records"]),
                    "Interval (min)": group.get("rotation_interval_minutes", "Default")
                })
    
    if not groups_data:
        print("No rotation groups configured.")
        return

    headers = {
        "Account": "Account",
        "Zone": "Zone",
        "Group Name": "Group Name",
        "Records": "Records",
        "Interval (min)": "Interval (min)"
    }
    display_as_table(groups_data, headers)

def add_rotation_group_menu():
    data = load_config()
    if not data["accounts"]:
        print("❌ No accounts available. Please add an account first.")
        return

    acc = select_from_list(data["accounts"], "Select an account:")
    if not acc:
        return

    try:
        cf_api = CloudflareAPI(acc["api_token"])
        zones_from_cf = list(cf_api.list_zones())
        if not zones_from_cf:
            print("❌ No zones found for this account in Cloudflare.")
            return
        
        zones_for_selection = [{"id": zone.id, "name": zone.name} for zone in zones_from_cf]
        selected_zone_info = select_from_list(zones_for_selection, "Select a zone:")
        if not selected_zone_info:
            return

        zone_id = selected_zone_info['id']
        zone_domain = selected_zone_info['name']
        
        # Ensure the zone exists in local config, add if not
        zone = find_zone(acc, zone_domain)
        if not zone:
            if "zones" not in acc:
                acc["zones"] = []
            zone = {"domain": zone_domain, "zone_id": zone_id, "records": [], "rotation_groups": []}
            acc["zones"].append(zone)
            validate_and_save_config(data)
            logger.info(f"Zone '{zone_domain}' added to local config.")

        records_from_cf = [r for r in cf_api.list_dns_records(zone_id) if r.type in ['A', 'AAAA']]
        if len(records_from_cf) < 2:
            print("❌ You need at least two A or AAAA records in this zone to create a rotation group.")
            return

        print("\n--- Select Records for the Group (at least 2) ---")
        for i, record in enumerate(records_from_cf):
            print(f"{i+1}. {record.name} ({record.type}: {record.content})")
        
        selected_records = []
        while True:
            try:
                choices_str = input("👉 Enter the numbers of the records, separated by commas (e.g., 1,2,3): ")
                selected_indices = [int(i.strip()) - 1 for i in choices_str.split(',')]
                
                if any(i < 0 or i >= len(records_from_cf) for i in selected_indices):
                    print("❌ Invalid selection. Please enter numbers from the list.")
                    continue
                
                if len(set(selected_indices)) < 2:
                    print("❌ Please select at least two different records.")
                    continue

                selected_records = [records_from_cf[i] for i in selected_indices]
                break
            except ValueError:
                print("❌ Invalid input. Please enter numbers separated by commas.")

        record_names = [r.name for r in selected_records]
        group_name = get_validated_input("Enter a name for this rotation group: ", lambda s: s.strip(), "Group name cannot be empty.")
        rotation_interval = get_rotation_interval()

        add_rotation_group(acc['name'], zone_domain, group_name, record_names, rotation_interval)

    except APIError as e:
        logger.error(f"Cloudflare API Error: {e}")
        print(f"❌ Cloudflare API Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print(f"❌ An unexpected error occurred: {e}")

def edit_rotation_group_menu():
    data = load_config()
    all_groups = []
    for acc in data.get("accounts", []):
        for zone in acc.get("zones", []):
            for group in zone.get("rotation_groups", []):
                all_groups.append({
                    "account_name": acc["name"],
                    "zone_domain": zone["domain"],
                    "name": group["name"],
                    "records": group["records"]
                })

    if not all_groups:
        print("No rotation groups to edit.")
        return

    group_to_edit = select_from_list(all_groups, "Select a rotation group to edit:")
    if not group_to_edit:
        return

    print(f"\n--- Editing Group: {group_to_edit['name']} ---")
    print(f"Current records: {', '.join(group_to_edit['records'])}")
    
    # For simplicity, we'll ask for the new list of records from scratch.
    # A more advanced implementation might allow adding/removing single records.
    print("You will need to re-select all records for the group.")
    
    try:
        cf_api = CloudflareAPI(find_account(data, group_to_edit['account_name'])['api_token'])
        zone_id = find_zone(find_account(data, group_to_edit['account_name']), group_to_edit['zone_domain'])['zone_id']
        records_from_cf = [r for r in cf_api.list_dns_records(zone_id) if r.type in ['A', 'AAAA']]

        if len(records_from_cf) < 2:
            print("❌ Not enough A/AAAA records in the zone to form a group.")
            return

        print("\n--- Select New Records for the Group (at least 2) ---")
        for i, record in enumerate(records_from_cf):
            print(f"{i+1}. {record.name} ({record.type}: {record.content})")
        
        new_selected_records = []
        while True:
            try:
                choices_str = input("👉 Enter the numbers of the records, separated by commas, or press Enter to keep current: ")
                if not choices_str:
                    new_selected_records = None
                    break

                selected_indices = [int(i.strip()) - 1 for i in choices_str.split(',')]
                
                if any(i < 0 or i >= len(records_from_cf) for i in selected_indices):
                    print("❌ Invalid selection.")
                    continue
                if len(set(selected_indices)) < 2:
                    print("❌ Please select at least two different records.")
                    continue
                new_selected_records = [records_from_cf[i].name for i in selected_indices]
                break
            except ValueError:
                print("❌ Invalid input.")

        new_interval_str = input(f"Enter new interval (minutes, min 5, or 'none') or press Enter to keep current: ").strip()

        edit_rotation_group(
            group_to_edit['account_name'], 
            group_to_edit['zone_domain'], 
            group_to_edit['name'], 
            new_selected_records, 
            new_interval_str
        )

    except APIError as e:
        logger.error(f"Cloudflare API Error: {e}")
        print(f"❌ Cloudflare API Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print(f"❌ An unexpected error occurred: {e}")


def delete_rotation_group_menu():
    data = load_config()
    all_groups = []
    for acc in data.get("accounts", []):
        for zone in acc.get("zones", []):
            for group in zone.get("rotation_groups", []):
                all_groups.append({
                    "account_name": acc["name"],
                    "zone_domain": zone["domain"],
                    "name": group["name"]
                })

    if not all_groups:
        print("No rotation groups to delete.")
        return

    group_to_delete = select_from_list(all_groups, "Select a rotation group to delete:")
    if not group_to_delete:
        return

    if confirm_action(f"Are you sure you want to delete the rotation group '{group_to_delete['name']}'?"):
        delete_rotation_group(
            group_to_delete['account_name'],
            group_to_delete['zone_domain'],
            group_to_delete['name']
        )

def rotate_ips_between_records_management_menu():
    """Displays the menu for managing scheduled rotation between records."""
    while True:
        clear_screen()
        print("\n--- Rotate IPs Between Records (Scheduled) ---")
        list_rotation_groups()
        print("\n1. ➕ Create Scheduled Rotation Group")
        print("2. ✏️ Edit a Scheduled Rotation Group")
        print("3. 🗑️ Delete a Scheduled Rotation Group")
        print("4. 📄 View logs")
        print("0. ⬅️ Return to previous menu")
        print("-----------------------------------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            add_rotation_group_menu()
        elif choice == "2":
            edit_rotation_group_menu()
        elif choice == "3":
            delete_rotation_group_menu()
        elif choice == "4":
            data = load_config()
            all_groups = []
            for acc in data.get("accounts", []):
                for zone in acc.get("zones", []):
                    for group in zone.get("rotation_groups", []):
                        all_groups.append(group)
            
            if not all_groups:
                print("No rotation groups configured to view logs for.")
                input("\nPress Enter to return...")
                continue
            
            group_to_view = select_from_list(all_groups, "Select a group to view logs for:")
            if group_to_view:
                view_live_logs(record_name=group_to_view['name'])

        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print("❌ Invalid choice. Please select a valid option.")
        
        if choice in ["1", "2", "3"]:
            input("\nPress Enter to return...")

def rotate_based_on_list_of_ips_multi_record_menu():
    """Displays the management menu for Multi-Records global rotations."""
    while True:
        clear_screen()
        print("\n--- Rotate Based on a List of IPs (Multi-Records) ---")
        list_global_rotations()
        print("\n1. ➕ Add New Global Rotation")
        print("2. ✏️ Edit a Global Rotation")
        print("3. 🗑️ Delete a Global Rotation")
        print("4. 📄 View Logs")
        print("0. ⬅️ Return to previous menu")
        print("-----------------------------------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            add_global_rotation_menu()
        elif choice == "2":
            edit_global_rotation_menu()
        elif choice == "3":
            delete_global_rotation_menu()
        elif choice == "4":
            view_global_rotation_logs_menu()
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print("❌ Invalid choice. Please select a valid option.")
        
        if choice in ["1", "2", "3"]:
            input("\nPress Enter to return...")

def add_global_rotation_menu():
    """Menu for adding a new global rotation configuration."""
    clear_screen()
    print("\n--- Add New Global Rotation Configuration ---")

    data = load_config()
    if not data["accounts"]:
        print("❌ No accounts available. Please add an account first.")
        input("\nPress Enter to return...")
        return

    acc = select_from_list(data["accounts"], "Select an account:")
    if not acc:
        return

    try:
        cf_api = CloudflareAPI(acc["api_token"])
        zones_from_cf = list(cf_api.list_zones())
        if not zones_from_cf:
            print("❌ No zones found for this account in Cloudflare.")
            input("\nPress Enter to return...")
            return

        zones_for_selection = [{"id": zone.id, "name": zone.name} for zone in zones_from_cf]
        selected_zone_info = select_from_list(zones_for_selection, "Select a zone:")
        if not selected_zone_info:
            return

        zone_id = selected_zone_info['id']
        zone_name = selected_zone_info['name']
        records_from_cf = [r for r in cf_api.list_dns_records(zone_id) if r.type in ['A', 'AAAA']]

        if len(records_from_cf) < 1:
            print("❌ You need at least one A or AAAA record in this zone.")
            input("\nPress Enter to return...")
            return

        print("\n--- Select Records for Global Rotation ---")
        for i, record in enumerate(records_from_cf):
            print(f"{i+1}. {record.name} ({record.type}: {record.content})")

        selected_records = []
        while True:
            try:
                choices_str = input("👉 Enter the numbers of the records, separated by commas (e.g., 1,2,3): ")
                selected_indices = [int(i.strip()) - 1 for i in choices_str.split(',')]

                if any(i < 0 or i >= len(records_from_cf) for i in selected_indices):
                    print("❌ Invalid selection. Please enter numbers from the list.")
                    continue

                selected_records = [records_from_cf[i] for i in selected_indices]
                break
            except ValueError:
                print("❌ Invalid input. Please enter numbers separated by commas.")
        
        record_names = [r.name for r in selected_records]

        print("\n--- Enter Shared IP Pool ---")
        ip_pool = get_ip_list('A')

        if not ip_pool:
            print("❌ IP pool cannot be empty.")
            input("\nPress Enter to return...")
            return
            
        rotation_interval = get_rotation_interval()
        
        config_name = get_validated_input("Enter a name for this configuration: ", lambda s: s.strip(), "Configuration name cannot be empty.")

        state = load_state()
        if "global_rotations" not in state:
            state["global_rotations"] = {}
            
        state["global_rotations"][config_name] = {
            "account_name": acc["name"],
            "zone_id": zone_id,
            "zone_name": zone_name,
            "records": record_names,
            "ip_pool": ip_pool,
            "rotation_interval_minutes": rotation_interval,
            "rotation_index": 0,
            "last_rotated_at": 0
        }
        
        save_state(state)
        print(f"\n✅ Global rotation configuration '{config_name}' saved.")

    except APIError as e:
        logger.error(f"Cloudflare API Error: {e}")
        print(f"❌ Cloudflare API Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"❌ An unexpected error occurred: {e}")

def list_global_rotations():
    """Lists all configured global rotations."""
    state = load_state()
    if "global_rotations" not in state or not state["global_rotations"]:
        print("No global rotations configured.")
        return

    rotations_data = []
    for name, config in state["global_rotations"].items():
        rotations_data.append({
            "Name": name,
            "Account": config["account_name"],
            "Zone": config["zone_name"],
            "Records": summarize_list(config["records"]),
            "IP Pool": summarize_list(config["ip_pool"]),
            "Interval (min)": config["rotation_interval_minutes"]
        })
    
    headers = {
        "Name": "Name",
        "Account": "Account",
        "Zone": "Zone",
        "Records": "Records",
        "IP Pool": "IP Pool",
        "Interval (min)": "Interval (min)"
    }
    display_as_table(rotations_data, headers)

def edit_global_rotation_menu():
    """Menu for editing a global rotation configuration."""
    clear_screen()
    print("\n--- Edit Global Rotation Configuration ---")

    state = load_state()
    if "global_rotations" not in state or not state["global_rotations"]:
        print("No global rotations configured to edit.")
        input("\nPress Enter to return...")
        return

    rotations = list(state["global_rotations"].keys())
    
    print("Select a configuration to edit:")
    for i, name in enumerate(rotations):
        print(f"{i+1}. {name}")

    while True:
        try:
            choice = int(input("Enter your choice (number): "))
            if 1 <= choice <= len(rotations):
                config_name = rotations[choice-1]
                break
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
    config = state["global_rotations"][config_name]
    
    print(f"\n--- Editing '{config_name}' ---")
    
    print(f"Current records: {', '.join(config['records'])}")
    new_records_str = input("Enter new record names (comma separated) or press Enter to keep current: ").strip()
    if new_records_str:
        config['records'] = [name.strip() for name in new_records_str.split(',')]
        
    print(f"Current IP pool: {', '.join(config['ip_pool'])}")
    new_ip_pool_str = input("Enter new IP pool (comma separated) or press Enter to keep current: ").strip()
    if new_ip_pool_str:
        config['ip_pool'] = [ip.strip() for ip in new_ip_pool_str.split(',')]
        
    print(f"Current rotation interval: {config['rotation_interval_minutes']} minutes")
    new_interval = get_rotation_interval(optional=True)
    if new_interval is not None:
        config['rotation_interval_minutes'] = new_interval
        
    save_state(state)
    print(f"\n✅ Global rotation configuration '{config_name}' updated.")

def delete_global_rotation_menu():
    """Menu for deleting a global rotation configuration."""
    clear_screen()
    print("\n--- Delete Global Rotation Configuration ---")

    state = load_state()
    if "global_rotations" not in state or not state["global_rotations"]:
        print("No global rotations configured to delete.")
        input("\nPress Enter to return...")
        return

    rotations = list(state["global_rotations"].keys())
    
    print("Select a configuration to delete:")
    for i, name in enumerate(rotations):
        print(f"{i+1}. {name}")

    while True:
        try:
            choice = int(input("Enter your choice (number): "))
            if 1 <= choice <= len(rotations):
                config_name = rotations[choice-1]
                break
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
    if confirm_action(f"Are you sure you want to delete the global rotation configuration '{config_name}'?"):
        del state["global_rotations"][config_name]
        save_state(state)
        print(f"✅ Global rotation configuration '{config_name}' deleted.")
    else:
        print("Deletion cancelled.")

def view_global_rotation_logs_menu():
    """Menu for viewing logs for a global rotation configuration."""
    clear_screen()
    print("\n--- View Global Rotation Logs ---")

    state = load_state()
    if "global_rotations" not in state or not state["global_rotations"]:
        print("No global rotations configured to view logs for.")
        input("\nPress Enter to return...")
        return

    rotations = list(state["global_rotations"].keys())
    
    print("Select a configuration to view logs for:")
    for i, name in enumerate(rotations):
        print(f"{i+1}. {name}")

    while True:
        try:
            choice = int(input("Enter your choice (number): "))
            if 1 <= choice <= len(rotations):
                config_name = rotations[choice-1]
                break
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
    view_live_logs(record_name=config_name)


def rotator_tools_menu():
    """Displays the Rotator Tools submenu."""
    clear_screen()
    while True:
        print("\n--- IP Rotator Tools ---")
        print("1. 🔄 Rotate Based on a List of IPs (Single-Record)")
        print("2. 🌍 Rotate Based on a List of IPs (Multi-Records)")
        print("3. 🔀 Rotate IPs Between Records")
        print("0. ⬅️ Return to Main Menu")
        print("---------------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            rotate_based_on_list_of_ips_single_record_menu()
        elif choice == "2":
            rotate_based_on_list_of_ips_multi_record_menu()
        elif choice == "3":
            rotate_ips_between_records_management_menu()
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print("❌ Invalid choice. Please select a valid option.")

def list_accounts():
    """Lists all configured accounts, including the number of zones for each."""
    data = load_config()
    if not data["accounts"]:
        print("No accounts configured.")
        return

    accounts_data = []
    for acc in data["accounts"]:
        try:
            cf_api = CloudflareAPI(acc["api_token"])
            zones = list(cf_api.list_zones())
            zone_count = len(zones)
        except APIError as e:
            logger.error(f"Failed to fetch zones for account {acc['name']}: {e}")
            zone_count = "Error"
        
        accounts_data.append({"Name": acc["name"], "Zones": zone_count})

    print("\n--- Configured Accounts ---")
    display_as_table(accounts_data, headers={"Name": "Name", "Zones": "Zones"})

def account_management_menu():
    """Displays the Account Management submenu."""
    clear_screen()
    while True:
        print("\n--- 👤 Cloudflare Account Management ---")
        list_accounts()  # Display accounts at the top of the menu
        print("\n1. 👤 Add a New Cloudflare Account")
        print("2. ✏️ Edit an Existing Cloudflare Account")
        print("3. 🗑️ Delete a Cloudflare Account")
        print("0. ⬅️ Return to Main Menu")
        print("---------------------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            add_account()
        elif choice == "2":
            edit_account()
        elif choice == "3":
            delete_account()
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print("❌ Invalid choice. Please select a valid option.")

import time

def view_live_logs(record_name=None):
    """
    Displays historical and live logs from the application log file.
    Optionally filters for a specific record.
    """
    clear_screen()
    if record_name:
        print(f"\n--- Live Logs for: {record_name} ---")
    else:
        print("\n--- Live Application Logs ---")
    print("Press Ctrl+C to stop viewing.")

    log_file_path = os.path.join(LOGS_DIR, "app.log")
    
    try:
        with open(log_file_path, 'r') as f:
            # --- Display historical logs ---
            for line in f:
                if not record_name or record_name in line:
                    print(line, end='')
            
            # --- Wait for new logs ---
            print("\n--- Waiting for new logs... ---")
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                if not record_name or record_name in line:
                    print(line, end='')

    except FileNotFoundError:
        print("Log file not found. Logging may not be configured yet.")
        input("\nPress Enter to return...")
    except KeyboardInterrupt:
        print("\n--- Stopped viewing logs. ---")
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        print(f"An error occurred while trying to read the log file: {e}")
        input("\nPress Enter to return...")

def main_menu():
    # Define ANSI escape codes for colors
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

    # Fix for running as a script
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    try:
        from version import __version__
        version_str = f"Version: {__version__}"
    except ImportError:
        version_str = "Version: N/A"
    
    author_str = "Author: https://github.com/Issei-177013"

    # Embed ASCII art
    art = """

 ██████╗███████╗    ██╗   ██╗████████╗██╗██╗     ███████╗
██╔════╝██╔════╝    ██║   ██║╚══██╔══╝██║██║     ██╔════╝
██║     █████╗█████╗██║   ██║   ██║   ██║██║     ███████╗
██║     ██╔══╝╚════╝██║   ██║   ██║   ██║██║     ╚════██║
╚██████╗██║         ╚██████╔╝   ██║   ██║███████╗███████║
 ╚═════╝╚═╝          ╚═════╝    ╚═╝   ╚═╝╚══════╝╚══════╝
                                                              
"""
    
    while True:
        clear_screen() # Clear screen on each loop iteration
        print(f"{YELLOW}{art}{RESET}")
        # Print author and version after the art
        print(f"{CYAN}{author_str}{RESET}")
        print(f"{CYAN}{version_str}{RESET}")
        
        print("===================================")

        print("\n--- Main Menu ---")
        print("1. 👤 Manage Cloudflare Accounts")
        print("2. 🔄 IP Rotator Tools")
        print("3. 📄 View Application Logs")
        print("0. 🚪 Exit")
        print("-----------------")

        choice = input("👉 Enter your choice: ").strip()
        
        if choice == "1":
            account_management_menu()
        elif choice == "2":
            rotator_tools_menu()
        elif choice == "3":
            view_live_logs()
        elif choice == "0":
            if confirm_action("Are you sure you want to exit?"):
                logger.info("Exiting Cloudflare Utils Manager.")
                break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print("❌ Invalid choice. Please select a valid option.")

def main():
    ensure_root()
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n👋 Exiting Cloudflare Utils Manager. Goodbye!")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
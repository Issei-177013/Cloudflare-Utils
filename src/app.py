import os
import sys
from .config import load_config, validate_and_save_config, find_account, find_zone, find_record, CONFIG_PATH
from .cloudflare_api import CloudflareAPI
from .dns_manager import add_record as add_record_to_config, delete_record as delete_record_from_config, edit_record as edit_record_in_config, edit_account_in_config, delete_account_from_config
from .ip_rotator import rotate_ips_between_records
from .input_helper import get_validated_input, get_ip_list, get_record_type, get_rotation_interval
from .validator import is_valid_domain, is_valid_zone_id, is_valid_record_name
from .logger import logger, LOGS_DIR
from .display import display_as_table
from cloudflare import APIError

def clear_screen():
    """Clears the terminal screen."""
    # For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # For macOS and Linux
    else:
        _ = os.system('clear')

def check_config_permissions():
    """Checks if the config file exists and is writable."""
    if not os.path.exists(CONFIG_PATH):
        logger.error(f"Config file not found at {CONFIG_PATH}.")
        print("Please ensure the program is installed correctly using install.sh.")
        sys.exit(1)
    
    if not os.access(CONFIG_PATH, os.W_OK):
        logger.error(f"Config file at {CONFIG_PATH} is not writable.")
        print(f"Please check the file permissions or try running the script with sudo if appropriate:")
        print(f"  sudo python3 {os.path.abspath(__file__)}")
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
                    "IPs": ", ".join(record.get("ips", [])),
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


def rotate_based_on_ip_list_menu():
    """Displays the submenu for rotation based on a list of IPs."""
    while True:
        clear_screen()
        print("\n--- DNS Record Rotation Management ---")
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


def rotate_ips_between_records_menu():
    """Menu for shuffling IPs between multiple DNS records."""
    clear_screen()
    print("\n--- Rotate IPs Between DNS Records ---")
    
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
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
        records_from_cf = [r for r in cf_api.list_dns_records(zone_id) if r.type in ['A', 'AAAA']]

        if not records_from_cf or len(records_from_cf) < 2:
            print("❌ You need at least two A or AAAA records in this zone to Rotate IPs.")
            input("\nPress Enter to return...")
            return

        print("\n--- Select Records to Rotate (at least 2) ---")
        for i, record in enumerate(records_from_cf):
            print(f"{i+1}. {record.name} ({record.type}: {record.content})")
        
        while True:
            try:
                choices_str = input("👉 Enter the numbers of the records to Rotate, separated by commas (e.g., 1,2,3): ")
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

        print("\n--- You have selected: ---")
        for record in selected_records:
            print(f"- {record.name} ({record.type}: {record.content})")

        if confirm_action("\nAre you sure you want to Rotate the IPs for these records?"):
            rotate_ips_between_records(cf_api, zone_id, records_from_cf, selected_indices)
            print("\n✅ IP shuffling process completed.")
        else:
            print("❌ IP shuffling cancelled.")
        
        input("\nPress Enter to return...")

    except APIError as e:
        logger.error(f"Cloudflare API Error in Rotate_ips_menu: {e}")
        print(f"❌ Cloudflare API Error: {e}")
        input("\nPress Enter to return...")
    except Exception as e:
        logger.error(f"An unexpected error occurred in Rotate_ips_menu: {e}")
        print(f"❌ An unexpected error occurred: {e}")
        input("\nPress Enter to return...")


def rotator_tools_menu():
    """Displays the Rotator Tools submenu."""
    clear_screen()
    while True:
        print("\n--- IP Rotator Tools ---")
        print("1. 🔄 Rotate Based on a List of IPs")
        print("2. 🔀 Rotate IPs Between Records")
        print("0. ⬅️ Return to Main Menu")
        print("---------------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            rotate_based_on_ip_list_menu()
        elif choice == "2":
            rotate_ips_between_records_menu()
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
    check_config_permissions() # Check permissions at the start of the menu

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
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n👋 Exiting Cloudflare Utils Manager. Goodbye!")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
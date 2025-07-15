import os
import sys
from .config import load_config, validate_and_save_config, find_account, find_zone, find_record, CONFIG_PATH
from .cloudflare_api import CloudflareAPI
from .dns_manager import add_record as add_record_to_config, delete_record as delete_record_from_config, edit_record as edit_record_in_config, edit_account_in_config, delete_account_from_config
from .input_helper import get_validated_input, get_ip_list, get_record_type, get_rotation_interval
from .validator import is_valid_domain, is_valid_zone_id, is_valid_record_name
from .logger import app_logger
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
        app_logger.error(f"Config file not found at {CONFIG_PATH}.")
        print("Please ensure the program is installed correctly using install.sh.")
        sys.exit(1)
    
    if not os.access(CONFIG_PATH, os.W_OK):
        app_logger.error(f"Config file at {CONFIG_PATH} is not writable.")
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
        app_logger.warning("Account already exists")
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
            app_logger.error(f"Cloudflare API Error on token verification: {e}")
            print(f"❌ Invalid Token. Cloudflare API Error: {e}")
            if not confirm_action("Try again?"):
                app_logger.warning("User aborted account creation.")
                return

    data["accounts"].append({"name": name, "api_token": token, "zones": []})
    if validate_and_save_config(data):
        app_logger.info(f"Account '{name}' added.")
        print("✅ Account added")

def edit_account():
    data = load_config()
    if not data["accounts"]:
        app_logger.warning("No accounts available.")
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
        app_logger.warning("No accounts available.")
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to delete:")
    if not acc:
        return

    if confirm_action(f"Are you sure you want to delete the account '{acc['name']}'?"):
        delete_account_from_config(acc['name'])
        app_logger.info(f"Account '{acc['name']}' deleted.")
    else:
        app_logger.info("Deletion cancelled.")

def add_record():
    data = load_config()
    if not data["accounts"]:
        app_logger.warning("No accounts available.")
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
            app_logger.warning(f"No zones found for account '{acc['name']}' in Cloudflare.")
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
            app_logger.info(f"Zone '{zone_domain}' added to local config.")
        else:
            app_logger.info(f"Zone '{zone_domain}' already exists in local config.")

    except APIError as e:
        app_logger.error(f"Cloudflare API Error fetching zones: {e}")
        print("❌ Could not fetch zones from Cloudflare.")
        return

    record_name = None
    try:
        cf_api = CloudflareAPI(acc["api_token"])
        zone_id = zone["zone_id"]
        app_logger.info(f"Fetching records for zone {zone['domain']}...")
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
                        app_logger.info(f"Using existing record: {record_name}")
                        break
                    elif choice == len(records_from_cf) + 1:
                        app_logger.info("Manual record name entry selected.")
                        break
                    else:
                        print("❌ Invalid choice.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
        else:
            app_logger.info(f"No existing records found in Cloudflare for zone {zone['domain']}. Proceeding with manual entry.")

    except APIError as e:
        app_logger.error(f"Cloudflare API Error fetching records: {e}")
        print("⚠️ Proceeding with manual record name entry.")
    except Exception as e:
        app_logger.error(f"An unexpected error occurred: {e}")
        print("⚠️ Proceeding with manual record name entry.")

    if not record_name:
        record_name = get_validated_input(
            "Record name (e.g., vpn.example.com): ",
            is_valid_record_name,
            "Invalid record name."
        )

    if find_record(zone, record_name):
        app_logger.warning(f"Record '{record_name}' already exists locally.")
        print("ℹ️ To update, please delete and re-add it.")
        return

    rec_type = get_record_type()
    ip_list = get_ip_list(rec_type)
    rotation_interval_minutes = get_rotation_interval()

    add_record_to_config(acc['name'], zone['domain'], record_name, rec_type, ip_list, rotation_interval_minutes)
    app_logger.info(f"Record '{record_name}' added to zone '{zone['domain']}'.")

def list_records_from_config():
    data = load_config()
    if not data["accounts"]:
        app_logger.info("No accounts to display.")
        print("No accounts configured. Please add an account first.")
        return

    print("\n--- Records Configured for Rotation ---")
    for acc_idx, acc in enumerate(data["accounts"]):
        print(f"\n[{acc_idx+1}] 🧾 Account: {acc['name']}")
        if not acc.get("zones"):
            print("  ℹ️ No zones configured for this account.")
            continue

        for zone_idx, zone in enumerate(acc["zones"]):
            print(f"  [{zone_idx+1}] 🌐 Zone: {zone['domain']}")
            if not zone.get("records"):
                print("    ℹ️ No records configured in this zone.")
                continue

            for rec_idx, record in enumerate(zone["records"]):
                interval = record.get('rotation_interval_minutes', 'Default (30)')
                ips = ', '.join(record.get('ips', []))
                print(f"    [{rec_idx+1}] 📌 Record: {record['name']} | Type: {record['type']} | IPs: {ips} | Interval: {interval} min")
    print("----------------------------------------")


def list_all():
    data = load_config()
    if not data["accounts"]:
        app_logger.info("No accounts to display.")
        print("No accounts configured. Please add an account first.")
        return

    print("\n--- All Accounts, Zones, and Records ---")
    for acc_idx, acc in enumerate(data["accounts"]):
        print(f"\n[{acc_idx+1}] 🧾 Account: {acc['name']}")
        try:
            cf_api = CloudflareAPI(acc["api_token"])
            zones_from_cf = cf_api.list_zones()
            
            zones_for_display = list(zones_from_cf)
            if not zones_for_display:
                print("  ℹ️ No zones found in this Cloudflare account.")
                continue

            for zone_idx, cf_zone in enumerate(zones_for_display):
                print(f"  [{zone_idx+1}] 🌐 Zone: {cf_zone.name} (ID: {cf_zone.id})")
                
                # Find local records for this zone to display rotation info
                local_zone_config = find_zone(acc, cf_zone.name)
                
                records_from_cf = cf_api.list_dns_records(cf_zone.id)
                records_for_display = list(records_from_cf)

                if not records_for_display:
                    print("    ℹ️ No DNS records found in this zone.")
                    continue

                for rec_idx, cf_record in enumerate(records_for_display):
                    rotation_info = ""
                    if local_zone_config:
                        local_record_config = find_record(local_zone_config, cf_record.name)
                        if local_record_config:
                            interval = local_record_config.get('rotation_interval_minutes', 'Default (30)')
                            ips = ', '.join(local_record_config.get('ips', []))
                            rotation_info = f" | 🔄 Rotation Config: {ips} every {interval} min"
                    
                    print(f"    [{rec_idx+1}] 📌 Record: {cf_record.name} | Type: {cf_record.type} | Content: {cf_record.content}{rotation_info}")

        except APIError as e:
            app_logger.error(f"Cloudflare API Error for account '{acc['name']}': {e}")
            print(f"  ❌ Error fetching data for this account: {e}")
            continue
    print("----------------------------------------")

def delete_record():
    data = load_config()
    if not data["accounts"]:
        app_logger.warning("No accounts available.")
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to delete a record from:")
    if not acc:
        return

    if not acc["zones"]:
        app_logger.warning(f"No zones available in account '{acc['name']}'.")
        print(f"❌ No zones available in account '{acc['name']}'.")
        return

    zone = select_from_list(acc["zones"], f"Select a zone in '{acc['name']}' to delete a record from:")
    if not zone:
        return

    if not zone["records"]:
        app_logger.warning(f"No records available in zone '{zone['domain']}'.")
        print(f"❌ No records available in zone '{zone['domain']}'.")
        return

    record_to_delete = select_from_list(zone["records"], f"Select a record in '{zone['domain']}' to delete:")
    if not record_to_delete:
        return

    if confirm_action(f"Are you sure you want to delete the record '{record_to_delete['name']}' from zone '{zone['domain']}'?"):
        delete_record_from_config(acc['name'], zone['domain'], record_to_delete['name'])
        app_logger.info(f"Record '{record_to_delete['name']}' deleted from zone '{zone['domain']}'.")
    else:
        app_logger.info("Deletion cancelled.")

def edit_record():
    data = load_config()
    if not data["accounts"]:
        app_logger.warning("No accounts available.")
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to edit a record in:")
    if not acc:
        return

    if not acc["zones"]:
        app_logger.warning(f"No zones available in account '{acc['name']}'.")
        print(f"❌ No zones available in account '{acc['name']}'.")
        return

    zone = select_from_list(acc["zones"], f"Select a zone in '{acc['name']}' to edit a record in:")
    if not zone:
        return

    if not zone["records"]:
        app_logger.warning(f"No records available in zone '{zone['domain']}'.")
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
    app_logger.info(f"Record '{record_to_edit['name']}' in zone '{zone['domain']}' updated.")

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
    clear_screen()
    while True:
        print("\n--- Rotate Based on a List of IPs ---")
        print("1. 📝 Add Record to Rotate")
        print("2. ✏️ Edit Record to Rotate")
        print("3. 🗑️ Delete Record to Rotate")
        print("4. 📋 List Records to Rotate")
        print("0. ⬅️ Back to Rotator Tools")
        print("------------------------------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            add_record()
        elif choice == "2":
            edit_record()
        elif choice == "3":
            delete_record()
        elif choice == "4":
            list_records_from_config()
        elif choice == "0":
            break
        else:
            app_logger.warning(f"Invalid choice: {choice}")
            print("❌ Invalid choice. Please select a valid option.")


def rotator_tools_menu():
    """Displays the Rotator Tools submenu."""
    clear_screen()
    while True:
        print("\n--- Rotator Tools ---")
        print("1. 🔄 Rotate Based on a List of IPs")
        print("0. ⬅️ Back to Main Menu")
        print("---------------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            rotate_based_on_ip_list_menu()
        elif choice == "0":
            break
        else:
            app_logger.warning(f"Invalid choice: {choice}")
            print("❌ Invalid choice. Please select a valid option.")

def account_management_menu():
    """Displays the Account Management submenu."""
    clear_screen()
    while True:
        print("\n--- 👤 Account Management ---")
        print("1. 👤 Add Cloudflare Account")
        print("2. ✏️ Edit Cloudflare Account")
        print("3. 🗑️ Delete Cloudflare Account")
        print("0. ⬅️ Back to Main Menu")
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
            app_logger.warning(f"Invalid choice: {choice}")
            print("❌ Invalid choice. Please select a valid option.")

def main_menu():
    clear_screen() # Clear the screen at the very beginning
    check_config_permissions() # Check permissions at the start of the menu

    # Define ANSI escape codes for colors
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

    # Import version and set author
    try:
        from ..version import __version__
        version_str = f"Version: {__version__}"
    except ImportError:
        version_str = "Version: N/A"
    
    author_str = "Author: Issei-177013"

    # Embed ASCII art
    art = """

 ██████╗███████╗    ██╗   ██╗████████╗██╗██╗     ███████╗
██╔════╝██╔════╝    ██║   ██║╚══██╔══╝██║██║     ██╔════╝
██║     █████╗█████╗██║   ██║   ██║   ██║██║     ███████╗
██║     ██╔══╝╚════╝██║   ██║   ██║   ██║██║     ╚════██║
╚██████╗██║         ╚██████╔╝   ██║   ██║███████╗███████║
 ╚═════╝╚═╝          ╚═════╝    ╚═╝   ╚═╝╚══════╝╚══════╝
                                                              
"""
    print(f"{YELLOW}{art}{RESET}")
    # Print author and version after the art
    print(f"{CYAN}{author_str}{RESET}")
    print(f"{CYAN}{version_str}{RESET}")
    
    print("===================================")
    print("🚀 Cloudflare Utils Manager 🚀")
    print("===================================")

    while True:
        print("\n--- Main Menu ---")
        print("1. 👤 Account Management")
        print("2. 🔄 Rotator Tools")
        print("0. 🚪 Exit")
        print("-----------------")

        choice = input("👉 Enter your choice: ").strip()
        
        if choice == "1":
            account_management_menu()
        elif choice == "2":
            rotator_tools_menu()
        elif choice == "0":
            if confirm_action("Are you sure you want to exit?"):
                app_logger.info("Exiting Cloudflare Utils Manager.")
                break
        else:
            app_logger.warning(f"Invalid choice: {choice}")
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

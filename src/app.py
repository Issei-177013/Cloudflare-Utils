import os
import sys
import logging
from .config import load_config, validate_and_save_config, find_account, find_zone, find_record, CONFIG_PATH
from .cloudflare_api import CloudflareAPI
from .dns_manager import add_record as add_record_to_config, delete_record as delete_record_from_config, edit_record as edit_record_in_config
from .input_helper import get_validated_input, get_ip_list, get_record_type, get_rotation_interval
from .validator import is_valid_domain, is_valid_zone_id, is_valid_record_name
from cloudflare import APIError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.error(f"Config file not found at {CONFIG_PATH}.")
        print("Please ensure the program is installed correctly using install.sh.")
        sys.exit(1)
    
    if not os.access(CONFIG_PATH, os.W_OK):
        logging.error(f"Config file at {CONFIG_PATH} is not writable.")
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
    token = get_validated_input("Cloudflare API Token: ", lambda s: s.strip(), "API Token cannot be empty.")

    print("ℹ️ INFO: While a Global API Key will work, it's STRONGLY recommended to use a specific API Token.")
    print("Create one at: https://dash.cloudflare.com/profile/api-tokens (My Profile > API Tokens > Create Token).")
    print("This provides better security and scoped permissions.")

    if find_account(data, name):
        logging.warning("Account already exists")
        print("❌ Account already exists")
        return

    data["accounts"].append({"name": name, "api_token": token, "zones": []})
    if validate_and_save_config(data):
        logging.info(f"Account '{name}' added.")
        print("✅ Account added")

def add_zone():
    data = load_config()
    if not data["accounts"]:
        logging.warning("No accounts available.")
        print("❌ No accounts available. Please add an account first.")
        return
    
    acc = select_from_list(data["accounts"], "Select an account:")
    if not acc:
        return

    domain = get_validated_input(
        "Zone domain (e.g. example.com): ",
        is_valid_domain,
        "Invalid domain format."
    )
    zone_id = get_validated_input(
        "Zone ID: ",
        is_valid_zone_id,
        "Invalid Zone ID format. Must be a 32-character hexadecimal string."
    )

    if find_zone(acc, domain):
        logging.warning(f"Zone '{domain}' already exists in account '{acc['name']}'.")
        print("❌ Zone already exists")
        return

    acc["zones"].append({"domain": domain, "zone_id": zone_id, "records": []})
    if validate_and_save_config(data):
        logging.info(f"Zone '{domain}' added to account '{acc['name']}'.")
        print("✅ Zone added")

def add_record():
    data = load_config()
    if not data["accounts"]:
        logging.warning("No accounts available.")
        print("❌ No accounts available. Please add an account first.")
        return

    acc = select_from_list(data["accounts"], "Select an account:")
    if not acc:
        return

    if not acc["zones"]:
        logging.warning(f"No zones available in account '{acc['name']}'.")
        print("❌ No zones available in this account. Please add a zone first.")
        return

    zone = select_from_list(acc["zones"], "Select a zone:")
    if not zone:
        return

    record_name = None
    try:
        cf_api = CloudflareAPI(acc["api_token"])
        zone_id = zone["zone_id"]
        logging.info(f"Fetching records for zone {zone['domain']}...")
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
                        logging.info(f"Using existing record: {record_name}")
                        break
                    elif choice == len(records_from_cf) + 1:
                        logging.info("Manual record name entry selected.")
                        break
                    else:
                        print("❌ Invalid choice.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
        else:
            logging.info(f"No existing records found in Cloudflare for zone {zone['domain']}. Proceeding with manual entry.")

    except APIError as e:
        logging.error(f"Cloudflare API Error fetching records: {e}")
        print("⚠️ Proceeding with manual record name entry.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        print("⚠️ Proceeding with manual record name entry.")

    if not record_name:
        record_name = get_validated_input(
            "Record name (e.g., vpn.example.com): ",
            is_valid_record_name,
            "Invalid record name."
        )

    if find_record(zone, record_name):
        logging.warning(f"Record '{record_name}' already exists locally.")
        print("ℹ️ To update, please delete and re-add it.")
        return

    rec_type = get_record_type()
    ip_list = get_ip_list(rec_type)
    rotation_interval_minutes = get_rotation_interval()

    add_record_to_config(acc['name'], zone['domain'], record_name, rec_type, ip_list, rotation_interval_minutes)
    logging.info(f"Record '{record_name}' added to zone '{zone['domain']}'.")

def list_all():
    data = load_config()
    if not data["accounts"]:
        logging.info("No accounts, zones, or records to display.")
        return

    print("\n--- All Accounts, Zones, and Records ---")
    for acc_idx, acc in enumerate(data["accounts"]):
        print(f"\n[{acc_idx+1}] 🧾 Account: {acc['name']}")
        if not acc["zones"]:
            print("  ℹ️ No zones in this account.")
            continue
        for zone_idx, zone in enumerate(acc["zones"]):
            print(f"  [{zone_idx+1}] 🌐 Zone: {zone['domain']} (ID: {zone['zone_id']})")
            if not zone["records"]:
                print("    ℹ️ No records in this zone.")
                continue
            for rec_idx, r in enumerate(zone["records"]):
                interval_str = f" | Rotation Interval: {r.get('rotation_interval_minutes', 'Default (30)')} min"
                print(f"    [{rec_idx+1}] 📌 Record: {r['name']} | Type: {r['type']} | IPs: {', '.join(r['ips'])}{interval_str}")
    print("----------------------------------------")

def delete_record():
    data = load_config()
    if not data["accounts"]:
        logging.warning("No accounts available.")
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to delete a record from:")
    if not acc:
        return

    if not acc["zones"]:
        logging.warning(f"No zones available in account '{acc['name']}'.")
        print(f"❌ No zones available in account '{acc['name']}'.")
        return

    zone = select_from_list(acc["zones"], f"Select a zone in '{acc['name']}' to delete a record from:")
    if not zone:
        return

    if not zone["records"]:
        logging.warning(f"No records available in zone '{zone['domain']}'.")
        print(f"❌ No records available in zone '{zone['domain']}'.")
        return

    record_to_delete = select_from_list(zone["records"], f"Select a record in '{zone['domain']}' to delete:")
    if not record_to_delete:
        return

    if confirm_action(f"Are you sure you want to delete the record '{record_to_delete['name']}' from zone '{zone['domain']}'?"):
        delete_record_from_config(acc['name'], zone['domain'], record_to_delete['name'])
        logging.info(f"Record '{record_to_delete['name']}' deleted from zone '{zone['domain']}'.")
    else:
        logging.info("Deletion cancelled.")

def edit_record():
    data = load_config()
    if not data["accounts"]:
        logging.warning("No accounts available.")
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to edit a record in:")
    if not acc:
        return

    if not acc["zones"]:
        logging.warning(f"No zones available in account '{acc['name']}'.")
        print(f"❌ No zones available in account '{acc['name']}'.")
        return

    zone = select_from_list(acc["zones"], f"Select a zone in '{acc['name']}' to edit a record in:")
    if not zone:
        return

    if not zone["records"]:
        logging.warning(f"No records available in zone '{zone['domain']}'.")
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
    logging.info(f"Record '{record_to_edit['name']}' in zone '{zone['domain']}' updated.")

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
  ______  _______                __    __  .___________. __   __          _______.
 /      ||   ____|              |  |  |  | |           ||  | |  |        /       |
|  ,----'|  |__       ______    |  |  |  | `---|  |----`|  | |  |       |   (----`
|  |     |   __|     |______|   |  |  |  |     |  |     |  | |  |        \   \    
|  `----.|  |                   |  `--'  |     |  |     |  | |  `----.----)   |   
 \______||__|                    \______/      |__|     |__| |_______|_______/    
                                                                                  
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
        print("1. 👤 Add Account")
        print("2. 🌍 Add Zone to Account")
        print("3. 📝 Add Record to Zone")
        print("4. ✏️ Edit Record in Zone")
        print("5. 🗑️ Delete Record from Zone")
        print("6. 📋 List All Records")
        print("7. 🚪 Exit")
        print("-----------------")

        choice = input("👉 Enter your choice: ").strip()
        
        if choice == "1":
            add_account()
        elif choice == "2":
            add_zone()
        elif choice == "3":
            add_record()
        elif choice == "4":
            edit_record()
        elif choice == "5":
            delete_record()
        elif choice == "6":
            list_all()
        elif choice == "7":
            if confirm_action("Are you sure you want to exit?"):
                logging.info("Exiting Cloudflare Utils Manager.")
                break
        else:
            logging.warning(f"Invalid choice: {choice}")
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

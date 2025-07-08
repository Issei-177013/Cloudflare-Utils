#!/usr/bin/env python3
from config_manager import load_config, save_config, find_account, find_zone, find_record, CONFIG_PATH
from cloudflare import Cloudflare, APIError # Added for Cloudflare API interaction
import os
import sys # For exiting the program

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
        print(f"❌ Error: Config file not found at {CONFIG_PATH}.")
        print("Please ensure the program is installed correctly using install.sh.")
        sys.exit(1)
    
    if not os.access(CONFIG_PATH, os.W_OK):
        print(f"❌ Error: Config file at {CONFIG_PATH} is not writable.")
        print(f"Please check the file permissions or try running the script with sudo if appropriate:")
        print(f"  sudo python3 {os.path.abspath(__file__)}")
        sys.exit(1)
    
    # Further checks for JSON validity could be added here,
    # but load_config() will raise an exception if the file is malformed.
    # The current checks for existence and writability are the primary concerns for cli.py.

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

def input_list(prompt):
    return input(prompt).strip().split(',')

def add_account():
    data = load_config()
    name = input("Account name: ").strip()
    token = input("API Token: ").strip()
    if find_account(data, name):
        print("❌ Account already exists")
        return
    data["accounts"].append({"name": name, "api_token": token, "zones": []})
    save_config(data)
    print("✅ Account added")

def add_zone():
    data = load_config()
    if not data["accounts"]:
        print("❌ No accounts available. Please add an account first.")
        return
    
    acc = select_from_list(data["accounts"], "Select an account:")
    if not acc:
        return

    domain = input("Zone domain (e.g. example.com): ").strip()
    zone_id = input("Zone ID: ").strip()
    if find_zone(acc, domain):
        print("❌ Zone already exists")
        return
    acc["zones"].append({"domain": domain, "zone_id": zone_id, "records": []})
    save_config(data)
    print("✅ Zone added")

def add_record():
    data = load_config()
    if not data["accounts"]:
        print("❌ No accounts available. Please add an account first.")
        return

    acc = select_from_list(data["accounts"], "Select an account:")
    if not acc:
        return

    if not acc["zones"]:
        print("❌ No zones available in this account. Please add a zone first.")
        return

    zone = select_from_list(acc["zones"], "Select a zone:")
    if not zone:
        return

    # Attempt to fetch and display existing records for selection
    record_name = None
    try:
        cf = Cloudflare(api_token=acc["api_token"])
        zone_id = zone["zone_id"]
        print(f"🔄 Fetching records for zone {zone['domain']}...")
        records_from_cf_paginator = cf.dns.records.list(zone_id=zone_id)
        # Convert paginator object to a list to use len() and indexing
        actual_records_list = list(records_from_cf_paginator)
        
        if actual_records_list: # Check if the list is not empty
            print("\n--- Existing Records ---")
            for i, cf_record in enumerate(actual_records_list):
                print(f"{i+1}. {cf_record.name} (Type: {cf_record.type}, Content: {cf_record.content})")
            print(f"{len(actual_records_list)+1}. Enter a new record name manually")
            print("-------------------------")
            
            while True:
                try:
                    choice = int(input("👉 Select a record to use/update or choose manual entry: "))
                    if 1 <= choice <= len(actual_records_list):
                        record_name = actual_records_list[choice-1].name
                        print(f"ℹ️ Using existing record: {record_name}")
                        # Check if this record already exists in local config to prevent duplicate *local* entries
                        # but allow updating if it's just a Cloudflare record not yet in local config for this specific IP list.
                        # The original find_record check will still apply later if we decide to keep it as is.
                        break
                    elif choice == len(actual_records_list) + 1:
                        print("✍️ Manual record name entry selected.")
                        break
                    else:
                        print("❌ Invalid choice. Please enter a number from the list.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
        else:
            print(f"ℹ️ No existing records found in Cloudflare for zone {zone['domain']}. Proceeding with manual entry.")

    except APIError as e:
        print(f"❌ Cloudflare API Error fetching records: {e}")
        print("⚠️ Proceeding with manual record name entry.")
    except Exception as e: # Catch other potential errors like network issues
        print(f"❌ An unexpected error occurred while fetching records: {e}")
        print("⚠️ Proceeding with manual record name entry.")

    if not record_name: # If no record was selected from the list (or fetching failed)
        name_input = input("Record name (e.g. vpn.example.com): ").strip()
        if not name_input:
            print("❌ Record name cannot be empty.")
            return
        record_name = name_input
    
    # Check if the chosen/entered record name already exists in the local config for this zone
    if find_record(zone, record_name):
        # If we selected an existing CF record, this check might seem redundant,
        # but it's crucial if the user manually types a name that matches an existing local entry.
        # Also, the intention is to add a *new set of IPs* for rotation under this name.
        # The current structure implies one record entry in config per name.
        # For this feature, we are selecting a name, then defining IPs for it.
        # If the record *name* is already in our config, we should prevent adding it again.
        # The user should perhaps use an "update existing record" feature if that's the intent.
        # For now, maintaining the original check for local config duplicates.
        print(f"❌ Record '{record_name}' already exists in the local configuration for this zone.")
        print("ℹ️ If you want to change its IPs or other settings, consider deleting and re-adding, or a future 'update' feature.")
        return

    ip_list = input_list("Enter IPs (comma separated): ")
    rec_type = input("Record type (A/CNAME): ").strip().upper()
    proxied = input("Proxied (yes/no): ").strip().lower() == 'yes'
    
    rotation_interval_minutes_str = input("Rotation interval in minutes (optional, default 30): ").strip()
    rotation_interval_minutes = None
    if rotation_interval_minutes_str:
        try:
            rotation_interval_minutes = int(rotation_interval_minutes_str)
            if rotation_interval_minutes < 5: # Enforce minimum of 5 minutes
                print("❌ Rotation interval must be at least 5 minutes.")
                return
        except ValueError:
            print("❌ Invalid input for rotation interval. Must be a number.")
            return
    # If rotation_interval_minutes_str is empty, rotation_interval_minutes remains None (for default handling)

    record_data = {
        "name": record_name, # Use the determined record_name
        "type": rec_type,
        "ips": ip_list,
        "proxied": proxied
    }
    if rotation_interval_minutes is not None:
        record_data["rotation_interval_minutes"] = rotation_interval_minutes

    zone["records"].append(record_data)

    save_config(data)
    print("✅ Record added successfully!")

def list_all():
    data = load_config()
    if not data["accounts"]:
        print("ℹ️ No accounts, zones, or records to display.")
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
                proxied_status = "Yes" if r['proxied'] else "No"
                interval_str = f" | Rotation Interval: {r.get('rotation_interval_minutes', 'Default (30)')} min"
                print(f"    [{rec_idx+1}] 📌 Record: {r['name']} | Type: {r['type']} | IPs: {', '.join(r['ips'])} | Proxied: {proxied_status}{interval_str}")
    print("----------------------------------------")


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
        from version import __version__
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
        print("4. 📋 List All Records")
        print("5. 🚪 Exit")
        print("-----------------")

        choice = input("👉 Enter your choice: ").strip()
        
        if choice == "1":
            add_account()
        elif choice == "2":
            add_zone()
        elif choice == "3":
            add_record()
        elif choice == "4":
            list_all()
        elif choice == "5":
            if confirm_action("Are you sure you want to exit?"):
                print("👋 Exiting Cloudflare Utils Manager. Goodbye!")
                break
        else:
            print("❌ Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n👋 Exiting Cloudflare Utils Manager. Goodbye!")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
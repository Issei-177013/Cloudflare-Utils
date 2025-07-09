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
    print("0. Back") # Added "0. Back" option

    while True:
        try:
            choice_str = input("Enter your choice (number, 0 to go back): ") # Updated prompt
            choice = int(choice_str)
            if choice == 0: # Handle "0" to go back
                return None
            if 1 <= choice <= len(items):
                return items[choice-1]
            else:
                print("Invalid choice. Please enter a number from the list or 0 to go back.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def input_list(prompt):
    return input(prompt).strip().split(',')

def add_account():
    data = load_config()
    name = input("Account name: ").strip()
    token = input("Cloudflare API Token: ").strip()
    print("ℹ️ INFO: While a Global API Key will work, it's STRONGLY recommended to use a specific API Token.")
    print("Create one at: https://dash.cloudflare.com/profile/api-tokens (My Profile > API Tokens > Create Token).")
    print("This provides better security and scoped permissions.")
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

def delete_record():
    data = load_config()
    if not data["accounts"]:
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to delete a record from:")
    if not acc:
        return

    if not acc["zones"]:
        print(f"❌ No zones available in account '{acc['name']}'.")
        return

    zone = select_from_list(acc["zones"], f"Select a zone in '{acc['name']}' to delete a record from:")
    if not zone:
        return

    if not zone["records"]:
        print(f"❌ No records available in zone '{zone['domain']}'.")
        return

    record_to_delete = select_from_list(zone["records"], f"Select a record in '{zone['domain']}' to delete:")
    if not record_to_delete:
        return

    if confirm_action(f"Are you sure you want to delete the record '{record_to_delete['name']}' from zone '{zone['domain']}'?"):
        zone["records"].remove(record_to_delete)
        save_config(data)
        print(f"✅ Record '{record_to_delete['name']}' deleted successfully from local configuration.")
    else:
        print("ℹ️ Deletion cancelled.")

def edit_record():
    data = load_config()
    if not data["accounts"]:
        print("❌ No accounts available.")
        return

    acc = select_from_list(data["accounts"], "Select an account to edit a record in:")
    if not acc:
        return

    if not acc["zones"]:
        print(f"❌ No zones available in account '{acc['name']}'.")
        return

    zone = select_from_list(acc["zones"], f"Select a zone in '{acc['name']}' to edit a record in:")
    if not zone:
        return

    if not zone["records"]:
        print(f"❌ No records available in zone '{zone['domain']}'.")
        return

    record_to_edit = select_from_list(zone["records"], f"Select a record in '{zone['domain']}' to edit:")
    if not record_to_edit:
        return

    print(f"\n--- Editing Record: {record_to_edit['name']} ---")
    print(f"Current IPs: {', '.join(record_to_edit['ips'])}")
    new_ips_str = input(f"Enter new IPs (comma separated) or press Enter to keep current: ").strip()
    if new_ips_str:
        record_to_edit['ips'] = [ip.strip() for ip in new_ips_str.split(',')]

    print(f"Current Type: {record_to_edit['type']}")
    new_type = input(f"Enter new type (A/CNAME) or press Enter to keep current: ").strip().upper()
    if new_type:
        record_to_edit['type'] = new_type

    print(f"Current Proxied: {'Yes' if record_to_edit['proxied'] else 'No'}")
    new_proxied_str = input(f"Proxied (yes/no) or press Enter to keep current: ").strip().lower()
    if new_proxied_str:
        record_to_edit['proxied'] = new_proxied_str == 'yes'

    current_interval = record_to_edit.get('rotation_interval_minutes', 'Default (30)')
    print(f"Current Rotation Interval (minutes): {current_interval}")
    new_interval_str = input(f"Enter new interval (minutes, min 5, or 'none' to use default) or press Enter to keep current: ").strip()
    if new_interval_str:
        if new_interval_str.lower() == 'none':
            if 'rotation_interval_minutes' in record_to_edit:
                del record_to_edit['rotation_interval_minutes']
            print("ℹ️ Rotation interval set to default (30 minutes).")
        else:
            try:
                new_interval = int(new_interval_str)
                if new_interval < 5:
                    print("❌ Rotation interval must be at least 5 minutes. Value not changed.")
                else:
                    record_to_edit['rotation_interval_minutes'] = new_interval
            except ValueError:
                print("❌ Invalid input for interval. Must be a number or 'none'. Value not changed.")
    
    save_config(data)
    print(f"✅ Record '{record_to_edit['name']}' updated successfully.")

def manage_cloudflare_accounts():
    """Handles management of Cloudflare accounts."""
    while True:
        clear_screen()
        print("\n--- 🌐 Manage Cloudflare Accounts ---")
        data = load_config()
        accounts = data.get("accounts", [])

        if not accounts:
            print("No accounts configured yet.")
        else:
            print("Saved Cloudflare Accounts:")
            print("--------------------------------------------------------------------------")
            print(f"{'#':<3} {'Account Label':<30} {'API Token (Masked)':<25} {'Zones Count':<10}")
            print("--------------------------------------------------------------------------")
            for i, acc in enumerate(accounts):
                token = acc.get("api_token", "N/A")
                masked_token = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else token
                zones_count = len(acc.get("zones", []))
                print(f"{i+1:<3} {acc.get('name', 'N/A'):<30} {masked_token:<25} {zones_count:<10}")
            print("--------------------------------------------------------------------------")

        print("\nOptions:")
        print("1) Add new account")
        print("2) Edit existing account")
        print("3) Delete account")
        print("0) Back to main menu") # Changed from 4 to 0
        print("-----------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            add_new_account_workflow()
        elif choice == "2":
            edit_existing_account_workflow()
        elif choice == "3":
            delete_account_workflow()
        elif choice == "0": # Changed from 4 to 0
            break
        else:
            print("❌ Invalid choice. Please select a valid option.")
            input("Press Enter to continue...")

def add_new_account_workflow():
    """Handles the workflow for adding a new Cloudflare account."""
    clear_screen()
    print("\n--- ➕ Add New Cloudflare Account ---")
    data = load_config()
    
    account_label = input("Enter a label for this account (e.g., 'My Personal Account'): ").strip()
    if not account_label:
        print("❌ Account label cannot be empty.")
        input("Press Enter to return to account management...")
        return

    if find_account(data, account_label):
        print(f"❌ An account with the label '{account_label}' already exists.")
        input("Press Enter to return to account management...")
        return

    api_token = input("Enter your Cloudflare API Token: ").strip()
    if not api_token:
        print("❌ API Token cannot be empty.")
        input("Press Enter to return to account management...")
        return

    # Optional: Validate token by attempting to fetch a list of zones.
    # For now, we'll skip this step as per the task description (optional).
    # try:
    #     cf = Cloudflare(api_token=api_token)
    #     cf.zones.get() # Simple call to check token validity
    #     print("✅ API Token validated successfully.")
    # except APIError as e:
    #     print(f"❌ Invalid API Token. Cloudflare API Error: {e}")
    #     print("Please ensure the token is correct and has the necessary permissions.")
    #     input("Press Enter to return to account management...")
    #     return
    # except Exception as e:
    #     print(f"❌ An unexpected error occurred during token validation: {e}")
    #     input("Press Enter to return to account management...")
    #     return

    new_account = {"name": account_label, "api_token": api_token, "zones": []}
    data["accounts"].append(new_account)
    save_config(data)
    print(f"✅ Account '{account_label}' added successfully!")
    input("Press Enter to return to account management...")

def edit_existing_account_workflow():
    """Handles the workflow for editing an existing Cloudflare account."""
    clear_screen()
    print("\n--- ✏️ Edit Existing Cloudflare Account ---")
    data = load_config()
    accounts = data.get("accounts", [])

    if not accounts:
        print("No accounts configured yet to edit.")
        input("Press Enter to return to account management...")
        return

    print("Select an account to edit:")
    selected_account = select_from_list(accounts, "Your accounts:")
    if not selected_account:
        input("Press Enter to return to account management...")
        return

    original_label = selected_account['name']
    print(f"\nEditing account: {original_label}")

    # Edit Account Label
    new_label = input(f"Enter new label (current: '{selected_account['name']}', press Enter to keep): ").strip()
    if new_label and new_label != selected_account['name']:
        # Check if the new label already exists (and it's not the current account's original label if it hasn't changed yet)
        if find_account(data, new_label):
            print(f"❌ An account with the label '{new_label}' already exists. Label not changed.")
        else:
            selected_account['name'] = new_label
            print(f"✅ Account label updated to '{new_label}'.")
    elif not new_label:
        print("ℹ️ Account label kept as is.")

    # Edit API Token
    current_token = selected_account['api_token']
    masked_current_token = f"{current_token[:4]}...{current_token[-4:]}" if len(current_token) > 8 else current_token
    print(f"Current API Token (masked): {masked_current_token}")
    new_token = input("Enter new API Token (press Enter to keep current): ").strip()
    if new_token:
        # Optional: Add token validation here if desired
        selected_account['api_token'] = new_token
        print("✅ API Token updated.")
    else:
        print("ℹ️ API Token kept as is.")
    
    save_config(data)
    print("\n✅ Account details updated successfully (if changes were made).")
    input("Press Enter to return to account management...")

def delete_account_workflow():
    """Handles the workflow for deleting a Cloudflare account."""
    clear_screen()
    print("\n--- 🗑️ Delete Cloudflare Account ---")
    data = load_config()
    accounts = data.get("accounts", [])

    if not accounts:
        print("No accounts configured yet to delete.")
        input("Press Enter to return to account management...")
        return

    print("Select an account to delete:")
    account_to_delete = select_from_list(accounts, "Your accounts:")
    if not account_to_delete:
        input("Press Enter to return to account management...")
        return

    # Confirm deletion
    if confirm_action(f"Are you sure you want to delete the account '{account_to_delete['name']}'? This will also remove all associated zones and records from this application's configuration."):
        accounts.remove(account_to_delete)
        save_config(data)
        print(f"✅ Account '{account_to_delete['name']}' and its associated data deleted successfully from the configuration.")
    else:
        print("ℹ️ Account deletion cancelled.")
    
    input("Press Enter to return to account management...")

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
        print("1. 🌍 Add Zone to Account")
        print("2. 📝 Add Record to Zone")
        print("3. ✏️ Edit Record in Zone")
        print("4. 🗑️ Delete Record from Zone")
        print("5. 📋 List All Records")
        print("6. 🌐 Manage Cloudflare Accounts")
        print("0. 🚪 Exit")
        print("-----------------")

        choice = input("👉 Enter your choice: ").strip()
        
        if choice == "1":
            add_zone()
        elif choice == "2":
            add_record()
        elif choice == "3":
            edit_record() # Placeholder for now
        elif choice == "4":
            delete_record() # Placeholder for now
        elif choice == "5":
            list_all()
        elif choice == "6":
            manage_cloudflare_accounts()
        elif choice == "0": # Changed from "8" to "0"
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
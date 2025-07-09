#!/usr/bin/env python3
import requests 
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

    # 🔄 Try fetching zones from Cloudflare to verify the token and get zone data
    print("🔍 Connecting to Cloudflare API and fetching zones...")
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get("https://api.cloudflare.com/client/v4/zones", headers=headers, params={"per_page": 50})
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        result = response.json()
        if not result.get("success"):
            raise Exception(result.get("errors", ["Unknown API error"]))

        zones = result.get("result", [])
        print(f"✅ {len(zones)} zones fetched successfully.")
    except Exception as e:
        print(f"❌ Failed to fetch zones: {e}")
        input("Press Enter to return to account management...")
        return

    # ✅ Store the new account with fetched zones
    new_account = {
        "name": account_label,
        "api_token": api_token,
        "zones": zones  # ⬅️ Saved zones directly
    }

    data["accounts"].append(new_account)
    save_config(data)

    print(f"✅ Account '{account_label}' added successfully with {len(zones)} zone(s).")
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
        print("1. 🌐 Manage Cloudflare Accounts")
        print("2. 🛠️ IP Rotator Tools")
        print("0. 🚪 Exit")
        print("-----------------")

        choice = input("👉 Enter your choice: ").strip()
        
        if choice == "1":
            manage_cloudflare_accounts()
        elif choice == "2":
            ip_rotator_tools_menu()
        elif choice == "0":
            if confirm_action("Are you sure you want to exit?"):
                print("👋 Exiting Cloudflare Utils Manager. Goodbye!")
                break
        else:
            print("❌ Invalid choice. Please select a valid option.")

def ip_rotator_tools_menu():
    """Displays the menu for IP Rotator Tools."""
    while True:
        clear_screen()
        print("\n--- 🛠️ IP Rotator Tools ---")
        print("1. Rotate a DNS Record using IP List")
        # Placeholder for future rotation tools
        print("0. Back to Main Menu")
        print("---------------------------")
        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            dns_rotation_menu() # New function to be created
        elif choice == "0":
            break
        else:
            print("❌ Invalid choice. Please select a valid option.")
            input("Press Enter to continue...")

def dns_rotation_menu():
    """Displays the menu for DNS Rotation features."""
    while True:
        clear_screen()
        print("\n--- 🔄 Rotate a DNS Record using IP List ---")
        print("1. ➕ Create New Rotation Rule")
        print("2. 📄 View Configured Rotations")
        print("3. ✏️ Edit Existing Rotation Settings")
        print("4. 🗑️ Delete Existing Rotation Rule")
        print("0. Back to IP Rotator Tools Menu")
        print("------------------------------------")
        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            create_new_rotation_rule()
        elif choice == "2":
            view_configured_rotations()
        elif choice == "3":
            edit_rotation_settings()
        elif choice == "4":
            delete_rotation_rule()
        elif choice == "0":
            break
        else:
            print("❌ Invalid choice. Please select a valid option.")
            input("Press Enter to continue...")

def view_configured_rotations(selection_mode=False):
    """Displays all configured rotation rules.
    If selection_mode is True, it allows selecting a rule and returns it.
    """
    config = load_config()
    rotations = config.get("rotations", [])
    if not rotations:
        print("ℹ️ No rotation rules configured yet.")
        if selection_mode:
            input("Press Enter to continue...")  # Allow returning to previous menu
            return None
        else:
            input("Press Enter to return to IP Rotator Menu...")
            return

    print("\n--- ⚙️ Configured Rotation Rules ---")
    print(f"{'#':<3} {'Account':<20} {'Zone':<25} {'Record':<30} {'Interval (min)':<15} {'IPs'}")
    print("-" * 120)
    for i, rule in enumerate(rotations):
        ips_str = ', '.join(rule.get('ip_list', []))
        if len(ips_str) > 40: # Truncate long IP lists for display
            ips_str = ips_str[:37] + "..."
        print(f"{i+1:<3} {rule.get('account_label', 'N/A'):<20} {rule.get('zone_name', 'N/A'):<25} {rule.get('record_name', 'N/A'):<30} {rule.get('rotate_interval_minutes', 'N/A'):<15} {ips_str}")
    print("-" * 120)

    if selection_mode:
        while True:
            try:
                choice_str = input("👉 Select a rule to edit/delete (number, 0 to go back): ")
                choice = int(choice_str)
                if choice == 0:
                    return None
                if 1 <= choice <= len(rotations):
                    return rotations[choice-1]
                else:
                    print("Invalid choice. Please enter a number from the list or 0.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    else:
        input("\nPress Enter to return to DNS Rotation Menu...")


def edit_rotation_settings():
    """Allows editing an existing rotation rule's IP list or interval."""
    clear_screen()
    print("\n--- ✏️ Edit Rotation Settings ---")
    
    selected_rule = view_configured_rotations(selection_mode=True)
    if not selected_rule:
        return

    config = load_config()
    # Find the actual rule in the config to modify it directly
    # This is safer than modifying a copy
    rule_to_edit = None
    for rule in config.get("rotations", []):
        # Assuming record_id and zone_id make a unique enough key for a rotation rule.
        # Or, if we had a unique ID per rule, that would be better.
        # For now, let's assume the selection by index is sufficient, and selected_rule is a reference
        # if view_configured_rotations returns parts of the original config list.
        # However, to be absolutely safe, let's find it by a unique identifier if possible,
        # or by comparing multiple fields if the returned object is a copy.
        # Python's list.index(selected_rule) might work if selected_rule is indeed an element from the list.
        # Let's find the index of the selected_rule to modify it in place.
        try:
            rule_index = config["rotations"].index(selected_rule)
            rule_to_edit = config["rotations"][rule_index]
        except ValueError:
            print("❌ Error: Could not find the selected rule in the configuration. This should not happen.")
            input("Press Enter to continue...")
            return

    print(f"\n--- Editing Rule for: {rule_to_edit['record_name']} in {rule_to_edit['zone_name']} ---")

    # Edit IP List
    current_ips_str = ', '.join(rule_to_edit.get('ip_list', []))
    print(f"Current IPs: {current_ips_str}")
    new_ips_str = input(f"Enter new IPs (comma separated) or press Enter to keep current: ").strip()
    if new_ips_str:
        new_ip_list = [ip.strip() for ip in new_ips_str.split(',') if ip.strip()]
        if new_ip_list:
            rule_to_edit['ip_list'] = new_ip_list
            print("✅ IP list updated.")
        else:
            print("ℹ️ IP list cannot be empty. Kept current IPs.")

    # Edit Rotation Interval
    current_interval = rule_to_edit.get('rotate_interval_minutes', 'N/A')
    print(f"Current Rotation Interval (minutes): {current_interval}")
    new_interval_str = input(f"Enter new interval (minutes, min 5) or press Enter to keep current: ").strip()
    if new_interval_str:
        try:
            new_interval = int(new_interval_str)
            if new_interval < 5:
                print("❌ Rotation interval must be at least 5 minutes. Value not changed.")
            else:
                rule_to_edit['rotate_interval_minutes'] = new_interval
                print("✅ Rotation interval updated.")
        except ValueError:
            print("❌ Invalid input for interval. Must be a number. Value not changed.")
    
    try:
        save_config(config)
        print(f"\n✅ Rotation rule for '{rule_to_edit['record_name']}' updated successfully!")
    except Exception as e:
        print(f"❌ Error saving updated rotation rule: {e}")

    input("Press Enter to return to DNS Rotation Menu...")


def delete_rotation_rule():
    """Allows deleting an existing rotation rule."""
    clear_screen()
    print("\n--- 🗑️ Delete Rotation Rule ---")

    selected_rule = view_configured_rotations(selection_mode=True)
    if not selected_rule:
        return

    if confirm_action(f"Are you sure you want to delete the rotation rule for '{selected_rule['record_name']}' in zone '{selected_rule['zone_name']}'?"):
        config = load_config()
        try:
            # Find and remove the rule.
            # Need to be careful if selected_rule is a copy.
            # It's better to find by some unique identifier or by iterating and comparing.
            rotations = config.get("rotations", [])
            rule_to_remove = None
            for rule in rotations:
                # This comparison might be fragile if the structure of selected_rule changes
                # or if there are float values etc. A unique ID per rule would be best.
                # For now, comparing key fields.
                if (rule.get('record_id') == selected_rule.get('record_id') and
                    rule.get('zone_id') == selected_rule.get('zone_id') and
                    rule.get('record_name') == selected_rule.get('record_name')): # Add more fields if necessary for uniqueness
                    rule_to_remove = rule
                    break
            
            if rule_to_remove:
                rotations.remove(rule_to_remove)
                save_config(config)
                print(f"✅ Rotation rule for '{selected_rule['record_name']}' deleted successfully.")
            else:
                # This case could happen if view_configured_rotations returns a copy and we can't find the original.
                # The .index() method used in edit_rotation_settings is generally safer if the list contains the exact objects.
                # Let's try removing by direct object comparison if `selected_rule` is indeed part of `rotations`
                try:
                    config["rotations"].remove(selected_rule) # This works if selected_rule is a direct reference
                    save_config(config)
                    print(f"✅ Rotation rule for '{selected_rule['record_name']}' deleted successfully.")
                except ValueError:
                    print("❌ Error: Could not find the selected rule in the configuration for deletion. This might indicate an issue with how rules are tracked.")

        except Exception as e:
            print(f"❌ Error deleting rotation rule: {e}")
    else:
        print("ℹ️ Deletion cancelled.")
    
    input("Press Enter to return to DNS Rotation Menu...")


def create_new_rotation_rule(): # Renamed from rotate_dns_record_with_custom_list
    """Manages DNS record rotation with a custom IP list."""
    clear_screen()
    print("\n--- ➕ Create New Rotation Rule ---") # Updated title
    config = load_config()

    if not config.get("accounts"):
        print("❌ No accounts configured. Please add an account first from the main menu.")
        input("Press Enter to continue...")
        return

    # Fetch zones using requests from all accounts
    all_zones_details = []
    print("🔄 Fetching zones from all accounts...")

    for acc_idx, account in enumerate(config["accounts"]):
        account_label = account.get("name", f"Account {acc_idx+1}")
        api_token = account.get("api_token")
        if not api_token:
            print(f"⚠️ Skipping account '{account_label}': No API token found.")
            continue

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get("https://api.cloudflare.com/client/v4/zones", headers=headers, params={"per_page": 50})
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

            result = response.json()
            if not result.get("success"):
                raise Exception(result.get("errors", ["Unknown API error"]))

            zones = result.get("result", [])
            for zone in zones:
                all_zones_details.append({
                    "name": zone["name"],
                    "id": zone["id"],
                    "account_label": account_label,
                    "api_token": api_token
                })

        except Exception as e:
            print(f"❌ Error fetching zones for '{account_label}': {e}")

    if not all_zones_details:
        print("❌ No zones found across all configured accounts.")
        input("Press Enter to continue...")
        return

    # Display zones
    print("\n--- Available Zones ---")
    print(f"{'#':<3} {'Zone Name':<30} {'Zone ID':<35} {'Associated Account':<25}")
    print("-" * 95)
    for i, zone_detail in enumerate(all_zones_details):
        print(f"{i+1:<3} {zone_detail['name']:<30} {zone_detail['id']:<35} {zone_detail['account_label']:<25}")
    print("-------------------------")
    print("0. Back")

    selected_zone_detail = None
    while True:
        try:
            choice = int(input("👉 Select a zone (number, 0 to go back): "))
            if choice == 0:
                return
            if 1 <= choice <= len(all_zones_details):
                selected_zone_detail = all_zones_details[choice-1]
                break
            else:
                print("Invalid choice. Please enter a number from the list or 0.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    if not selected_zone_detail:
        return

    # Fetch DNS records (A and AAAA)
    print(f"\n🔄 Fetching DNS records for zone '{selected_zone_detail['name']}'...")
    dns_records_details = []
    try:
        headers = {
            "Authorization": f"Bearer {selected_zone_detail['api_token']}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/zones/{selected_zone_detail['id']}/dns_records",
            headers=headers,
            params={"per_page": 100}
        )

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        records = response.json().get("result", [])
        for record in records:
            if record["type"] in ["A", "AAAA"]:
                dns_records_details.append({
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"],
                    "content": record["content"],
                    "proxied": record["proxied"]
                })

    except Exception as e:
        print(f"❌ Error fetching DNS records: {e}")
        input("Press Enter to continue...")
        return

    if not dns_records_details:
        print(f"❌ No A or AAAA records found in zone '{selected_zone_detail['name']}'.")
        input("Press Enter to continue...")
        return

    # Show available DNS records
    print("\n--- Available DNS Records (A/AAAA) ---")
    print(f"{'#':<3} {'Record Name':<40} {'Type':<6} {'Current IP':<20} {'Proxied?':<10}")
    print("-" * 85)
    for i, rec_detail in enumerate(dns_records_details):
        proxied_status = "Yes" if rec_detail['proxied'] else "No"
        print(f"{i+1:<3} {rec_detail['name']:<40} {rec_detail['type']:<6} {rec_detail['content']:<20} {proxied_status:<10}")
    print("--------------------------------------")
    print("0. Back")

    selected_record_detail = None
    while True:
        try:
            choice = int(input("👉 Select a record to rotate (number, 0 to go back): "))
            if choice == 0:
                return
            if 1 <= choice <= len(dns_records_details):
                selected_record_detail = dns_records_details[choice-1]
                break
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")

    if not selected_record_detail:
        return

    # Prompt for IPs
    print(f"\n--- Configuring Rotation for: {selected_record_detail['name']} ---")
    ip_list_str = input("Enter a list of IP addresses to rotate (comma-separated): ").strip()
    ip_list = [ip.strip() for ip in ip_list_str.split(",") if ip.strip()]
    if not ip_list:
        print("❌ IP list cannot be empty.")
        input("Press Enter to continue...")
        return

    # Prompt for interval
    while True:
        try:
            interval = int(input("Enter rotation interval in minutes (e.g., 30, minimum 5): "))
            if interval >= 5:
                break
            else:
                print("❌ Interval must be 5 minutes or more.")
        except ValueError:
            print("❌ Please enter a valid number.")

    # Save rule
    new_rotation_rule = {
        "account_label": selected_zone_detail['account_label'],
        "zone_id": selected_zone_detail['id'],
        "zone_name": selected_zone_detail['name'],
        "record_id": selected_record_detail['id'],
        "record_name": selected_record_detail['name'],
        "record_type": selected_record_detail['type'],
        "ip_list": ip_list,
        "rotate_interval_minutes": interval,
        "proxied": selected_record_detail['proxied']
    }

    config.setdefault("rotations", []).append(new_rotation_rule)
    try:
        save_config(config)
        print(f"\n✅ Rotation rule for '{selected_record_detail['name']}' saved successfully!")
    except Exception as e:
        print(f"❌ Error saving rotation rule: {e}")

    input("Press Enter to return to DNS Rotation Menu...")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n👋 Exiting Cloudflare Utils Manager. Goodbye!")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
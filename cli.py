#!/usr/bin/env python3
from config_manager import load_config, save_config, find_account, find_zone, find_record, CONFIG_PATH
import os
import sys # For exiting the program

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

    name = input("Record name (e.g. vpn.example.com): ").strip()
    if find_record(zone, name):
        print("❌ Record already exists")
        return
    ip_list = input_list("Enter IPs (comma separated): ")
    rec_type = input("Record type (A/CNAME): ").strip().upper()
    proxied = input("Proxied (yes/no): ").strip().lower() == 'yes'

    zone["records"].append({
        "name": name,
        "type": rec_type,
        "ips": ip_list,
        "proxied": proxied
    })

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
                print(f"    [{rec_idx+1}] 📌 Record: {r['name']} | Type: {r['type']} | IPs: {', '.join(r['ips'])} | Proxied: {proxied_status}")
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
    check_config_permissions() # Check permissions at the start of the menu
    
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
            if confirm_action("Add a new account?"):
                add_account()
        elif choice == "2":
            if confirm_action("Add a new zone?"):
                add_zone()
        elif choice == "3":
            if confirm_action("Add a new record?"):
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
    main_menu()
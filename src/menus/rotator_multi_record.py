"""
Multi-Record IP Rotation Menu.

This module provides the user interface for managing "global" rotation
configurations. This rotation strategy involves multiple DNS records sharing
a single pool of IP addresses, which are rotated across the records in a
synchronized, round-robin fashion.

These configurations are stored in the `state.json` file.
"""
from ..config import load_config, find_account
from ..cloudflare_api import CloudflareAPI
from ..state_manager import load_state, save_state
from ..input_helper import get_validated_input, get_ip_list, get_rotation_interval
from ..logger import logger
from ..display import display_as_table, summarize_list, print_slow, OPTION_SEPARATOR
from cloudflare import APIError
from .utils import clear_screen, select_from_list, confirm_action, view_live_logs

def add_global_rotation_menu():
    """
    Guides the user through creating a new multi-record rotation configuration.
    """
    clear_screen()
    print_slow("\n--- Add New Global Rotation Configuration ---")

    data = load_config()
    if not data["accounts"]:
        print_slow("❌ No accounts available. Please add an account first.")
        input("\nPress Enter to return...")
        return

    acc = select_from_list(data["accounts"], "Select an account:")
    if not acc:
        return

    try:
        cf_api = CloudflareAPI(acc["api_token"])
        zones_from_cf = list(cf_api.list_zones())
        if not zones_from_cf:
            print_slow("❌ No zones found for this account in Cloudflare.")
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
            print_slow("❌ You need at least one A or AAAA record in this zone.")
            input("\nPress Enter to return...")
            return

        print_slow("\n--- Select Records for Global Rotation ---")
        for i, record in enumerate(records_from_cf):
            print_slow(f"{i+1}. {record.name} ({record.type}: {record.content})")

        selected_records = []
        while True:
            try:
                choices_str = input("👉 Enter the numbers of the records, separated by commas (e.g., 1,2,3): ")
                selected_indices = [int(i.strip()) - 1 for i in choices_str.split(',')]

                if any(i < 0 or i >= len(records_from_cf) for i in selected_indices):
                    print_slow("❌ Invalid selection. Please enter numbers from the list.")
                    continue

                selected_records = [records_from_cf[i] for i in selected_indices]
                break
            except ValueError:
                print_slow("❌ Invalid input. Please enter numbers separated by commas.")
        
        record_names = [r.name for r in selected_records]

        print_slow("\n--- Enter Shared IP Pool ---")
        ip_pool = get_ip_list('A')

        if not ip_pool:
            print_slow("❌ IP pool cannot be empty.")
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
        print_slow(f"\n✅ Global rotation configuration '{config_name}' saved.")

    except APIError as e:
        logger.error(f"Cloudflare API Error: {e}")
        print_slow(f"❌ Cloudflare API Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        print_slow(f"❌ An unexpected error occurred: {e}")

def list_global_rotations():
    """
    Lists all configured multi-record ("global") rotations in a table.
    """
    state = load_state()
    if "global_rotations" not in state or not state["global_rotations"]:
        print_slow("No global rotations configured.")
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
    
    headers = [
        "Name",
        "Account",
        "Zone",
        "Records",
        "IP Pool",
        "Interval (min)"
    ]
    display_as_table(rotations_data, headers)

def edit_global_rotation_menu():
    """
    Guides the user through editing an existing multi-record rotation config.
    """
    clear_screen()
    print_slow("\n--- Edit Global Rotation Configuration ---")

    state = load_state()
    if "global_rotations" not in state or not state["global_rotations"]:
        print_slow("No global rotations configured to edit.")
        input("\nPress Enter to return...")
        return

    rotations = list(state["global_rotations"].keys())
    
    print_slow("Select a configuration to edit:")
    for i, name in enumerate(rotations):
        print_slow(f"{i+1}. {name}")

    while True:
        try:
            choice = int(input("Enter your choice (number): "))
            if 1 <= choice <= len(rotations):
                config_name = rotations[choice-1]
                break
            else:
                print_slow("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print_slow("Invalid input. Please enter a number.")
            
    config = state["global_rotations"][config_name]
    
    print_slow(f"\n--- Editing '{config_name}' ---")
    
    print_slow(f"Current records: {', '.join(config['records'])}")
    new_records_str = input("Enter new record names (comma separated) or press Enter to keep current: ").strip()
    if new_records_str:
        config['records'] = [name.strip() for name in new_records_str.split(',')]
        
    print_slow(f"Current IP pool: {', '.join(config['ip_pool'])}")
    new_ip_pool_str = input("Enter new IP pool (comma separated) or press Enter to keep current: ").strip()
    if new_ip_pool_str:
        config['ip_pool'] = [ip.strip() for ip in new_ip_pool_str.split(',')]
        
    print_slow(f"Current rotation interval: {config['rotation_interval_minutes']} minutes")
    new_interval = get_rotation_interval(optional=True)
    if new_interval is not None:
        config['rotation_interval_minutes'] = new_interval
        
    save_state(state)
    print_slow(f"\n✅ Global rotation configuration '{config_name}' updated.")

def delete_global_rotation_menu():
    """
    Guides the user through deleting a multi-record rotation configuration.
    """
    clear_screen()
    print_slow("\n--- Delete Global Rotation Configuration ---")

    state = load_state()
    if "global_rotations" not in state or not state["global_rotations"]:
        print_slow("No global rotations configured to delete.")
        input("\nPress Enter to return...")
        return

    rotations = list(state["global_rotations"].keys())
    
    print_slow("Select a configuration to delete:")
    for i, name in enumerate(rotations):
        print_slow(f"{i+1}. {name}")

    while True:
        try:
            choice = int(input("Enter your choice (number): "))
            if 1 <= choice <= len(rotations):
                config_name = rotations[choice-1]
                break
            else:
                print_slow("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print_slow("Invalid input. Please enter a number.")
            
    if confirm_action(f"Are you sure you want to delete the global rotation configuration '{config_name}'?"):
        del state["global_rotations"][config_name]
        save_state(state)
        print_slow(f"✅ Global rotation configuration '{config_name}' deleted.")
    else:
        print_slow("Deletion cancelled.")

def view_global_rotation_logs_menu():
    """
    Guides the user through selecting a multi-record rotation config to view its logs.
    """
    clear_screen()
    print_slow("\n--- View Global Rotation Logs ---")

    state = load_state()
    if "global_rotations" not in state or not state["global_rotations"]:
        print_slow("No global rotations configured to view logs for.")
        input("\nPress Enter to return...")
        return

    rotations = list(state["global_rotations"].keys())
    
    print_slow("Select a configuration to view logs for:")
    for i, name in enumerate(rotations):
        print_slow(f"{i+1}. {name}")

    while True:
        try:
            choice = int(input("Enter your choice (number): "))
            if 1 <= choice <= len(rotations):
                config_name = rotations[choice-1]
                break
            else:
                print_slow("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print_slow("Invalid input. Please enter a number.")
            
    view_live_logs(record_name=config_name)

def rotate_based_on_list_of_ips_multi_record_menu():
    """
    Displays the management menu for multi-record IP rotations.
    """
    while True:
        clear_screen()
        print_slow("\n--- Rotate Based on a List of IPs (Multi-Records) ---")
        list_global_rotations()
        print_slow("\n1. ➕ Add New Global Rotation")
        print_slow("2. ✏️ Edit a Global Rotation")
        print_slow("3. 🗑️ Delete a Global Rotation")
        print_slow("4. 📄 View Logs")
        print_slow("0. ⬅️ Return to previous menu")
        print_slow(OPTION_SEPARATOR)

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
            print_slow("❌ Invalid choice. Please select a valid option.")
        
        if choice in ["1", "2", "3"]:
            input("\nPress Enter to return...")
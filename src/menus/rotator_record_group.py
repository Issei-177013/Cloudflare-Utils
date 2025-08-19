"""
Rotation Group Management Menu.

This module provides the user interface for managing "rotation groups".
A rotation group is a set of DNS records within a zone whose IP addresses
are rotated among each other on a schedule. This is different from other
rotation methods as it uses the records' existing IPs rather than a
separate, predefined list.
"""
from ..config import load_config, validate_and_save_config, find_account, find_zone
from ..cloudflare_api import CloudflareAPI
from ..dns_manager import add_rotation_group, edit_rotation_group, delete_rotation_group
from ..input_helper import get_validated_input, get_rotation_interval
from ..logger import logger
from ..display import *
from cloudflare import APIError
from .utils import clear_screen, select_from_list, confirm_action, view_live_logs

def list_rotation_groups():
    """
    Lists all configured rotation groups in a table.
    """
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
        print_fast("No rotation groups configured.")
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
    """
    Guides the user through creating a new rotation group.
    """
    data = load_config()
    if not data["accounts"]:
        print_fast(f"{COLOR_ERROR}❌ No accounts available. Please add an account first.{RESET_COLOR}")
        return

    acc = select_from_list(data["accounts"], "Select an account:")
    if not acc:
        return

    try:
        cf_api = CloudflareAPI(acc["api_token"])
        zones_from_cf = list(cf_api.list_zones())
        if not zones_from_cf:
            print_fast(f"{COLOR_ERROR}❌ No zones found for this account in Cloudflare.{RESET_COLOR}")
            return
        
        zones_for_selection = [{"id": zone.id, "name": zone.name} for zone in zones_from_cf]
        selected_zone_info = select_from_list(zones_for_selection, "Select a zone:")
        if not selected_zone_info:
            return

        zone_id = selected_zone_info['id']
        zone_domain = selected_zone_info['name']
        
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
            print_fast(f"{COLOR_ERROR}❌ You need at least two A or AAAA records in this zone to create a rotation group.{RESET_COLOR}")
            return

        print_fast(f"\n{COLOR_TITLE}--- Select Records for the Group (at least 2) ---{RESET_COLOR}")
        for i, record in enumerate(records_from_cf):
            print_fast(f"{i+1}. {record.name} ({record.type}: {record.content})")
        
        selected_records = []
        while True:
            try:
                choices_str = input("👉 Enter the numbers of the records, separated by commas (e.g., 1,2,3): ")
                selected_indices = [int(i.strip()) - 1 for i in choices_str.split(',')]
                
                if any(i < 0 or i >= len(records_from_cf) for i in selected_indices):
                    print_fast(f"{COLOR_ERROR}❌ Invalid selection. Please enter numbers from the list.{RESET_COLOR}")
                    continue
                
                if len(set(selected_indices)) < 2:
                    print_fast(f"{COLOR_ERROR}❌ Please select at least two different records.{RESET_COLOR}")
                    continue

                selected_records = [records_from_cf[i] for i in selected_indices]
                break
            except ValueError:
                print_fast(f"{COLOR_ERROR}❌ Invalid input. Please enter numbers separated by commas.{RESET_COLOR}")

        record_names = [r.name for r in selected_records]
        group_name = get_validated_input("Enter a name for this rotation group: ", lambda s: s.strip(), "Group name cannot be empty.")
        rotation_interval = get_rotation_interval()

        add_rotation_group(acc['name'], zone_domain, group_name, record_names, rotation_interval)

    except APIError as e:
        logger.error(f"Cloudflare API Error: {e}")
        print_fast(f"{COLOR_ERROR}❌ Cloudflare API Error: {e}{RESET_COLOR}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print_fast(f"{COLOR_ERROR}❌ An unexpected error occurred: {e}{RESET_COLOR}")

def edit_rotation_group_menu():
    """
    Guides the user through editing an existing rotation group.
    """
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
        print_fast(f"{COLOR_WARNING}No rotation groups to edit.{RESET_COLOR}")
        return

    group_to_edit = select_from_list(all_groups, "Select a rotation group to edit:")
    if not group_to_edit:
        return

    print_fast(f"\n{COLOR_TITLE}--- Editing Group: {group_to_edit['name']} ---{RESET_COLOR}")
    print_fast(f"Current records: {', '.join(group_to_edit['records'])}")
    
    print_fast("You will need to re-select all records for the group.")
    
    try:
        cf_api = CloudflareAPI(find_account(data, group_to_edit['account_name'])['api_token'])
        zone_id = find_zone(find_account(data, group_to_edit['account_name']), group_to_edit['zone_domain'])['zone_id']
        records_from_cf = [r for r in cf_api.list_dns_records(zone_id) if r.type in ['A', 'AAAA']]

        if len(records_from_cf) < 2:
            print_fast(f"{COLOR_ERROR}❌ Not enough A/AAAA records in the zone to form a group.{RESET_COLOR}")
            return

        print_fast(f"\n{COLOR_TITLE}--- Select New Records for the Group (at least 2) ---{RESET_COLOR}")
        for i, record in enumerate(records_from_cf):
            print_fast(f"{i+1}. {record.name} ({record.type}: {record.content})")
        
        new_selected_records = []
        while True:
            try:
                choices_str = input("👉 Enter the numbers of the records, separated by commas, or press Enter to keep current: ")
                if not choices_str:
                    new_selected_records = None
                    break

                selected_indices = [int(i.strip()) - 1 for i in choices_str.split(',')]
                
                if any(i < 0 or i >= len(records_from_cf) for i in selected_indices):
                    print_fast(f"{COLOR_ERROR}❌ Invalid selection.{RESET_COLOR}")
                    continue
                if len(set(selected_indices)) < 2:
                    print_fast(f"{COLOR_ERROR}❌ Please select at least two different records.{RESET_COLOR}")
                    continue
                new_selected_records = [records_from_cf[i].name for i in selected_indices]
                break
            except ValueError:
                print_fast(f"{COLOR_ERROR}❌ Invalid input.{RESET_COLOR}")

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
        print_fast(f"{COLOR_ERROR}❌ Cloudflare API Error: {e}{RESET_COLOR}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print_fast(f"{COLOR_ERROR}❌ An unexpected error occurred: {e}{RESET_COLOR}")


def delete_rotation_group_menu():
    """
    Guides the user through deleting a rotation group.
    """
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
        print_fast(f"{COLOR_WARNING}No rotation groups to delete.{RESET_COLOR}")
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
    """
    Displays the main menu for managing scheduled rotation groups.
    """
    while True:
        clear_screen()
        print_fast(f"\n{COLOR_TITLE}--- Rotate IPs Between Records (Scheduled) ---{RESET_COLOR}")
        list_rotation_groups()
        print_slow("\n1. ➕ Create Scheduled Rotation Group")
        print_slow("2. ✏️ Edit a Scheduled Rotation Group")
        print_slow("3. 🗑️ Delete a Scheduled Rotation Group")
        print_slow("4. 📄 View logs")
        print_slow("0. ⬅️ Return to previous menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

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
                print_fast(f"{COLOR_WARNING}No rotation groups configured to view logs for.{RESET_COLOR}")
                input("\nPress Enter to return...")
                continue
            
            group_to_view = select_from_list(all_groups, "Select a group to view logs for:")
            if group_to_view:
                view_live_logs(record_name=group_to_view['name'])

        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
        
        if choice in ["1", "2", "3"]:
            input("\nPress Enter to return...")
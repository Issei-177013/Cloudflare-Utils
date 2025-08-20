"""
Single-Record IP Rotation Menu.

This module provides the user interface for managing IP rotation for individual
DNS records. Users can create, edit, delete, and view rotation configurations.
A single-record rotation involves one DNS record and a dedicated list of IPs
that are cycled through on a schedule.
"""
from ..config import load_config, validate_and_save_config, find_account, find_zone, find_record
from ..cloudflare_api import CloudflareAPI
from ..dns_manager import add_record as add_record_to_config, delete_record as delete_record_from_config, edit_record as edit_record_in_config
from ..input_helper import get_validated_input, get_ip_list, get_record_type, get_rotation_interval
from ..validator import is_valid_record_name
from ..logger import logger
from ..display import *
from ..error_handler import MissingPermissionError
from ..triggers import select_trigger
from cloudflare import APIError
from .utils import clear_screen, select_from_list, confirm_action, view_live_logs, get_schedule_config

def add_record():
    """
    Guides the user through adding a new single-record rotation configuration.
    """
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
        print_fast(f"{COLOR_ERROR}❌ No accounts available. Please add an account first.{RESET_COLOR}")
        return

    acc = select_from_list(data["accounts"], "Select an account:")
    if not acc:
        return

    try:
        cf_api = CloudflareAPI(acc["api_token"])
        zones_from_cf = cf_api.list_zones()
        
        zones_for_selection = [{"id": zone.id, "name": zone.name} for zone in zones_from_cf]

        if not zones_for_selection:
            logger.warning(f"No zones found for account '{acc['name']}' in Cloudflare.")
            print_fast(f"{COLOR_ERROR}❌ No zones available in this account. Please add a zone in your Cloudflare account first.{RESET_COLOR}")
            return

        selected_zone_info = select_from_list(zones_for_selection, "Select a zone from Cloudflare:")
        if not selected_zone_info:
            return

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
        print_fast(f"{COLOR_ERROR}❌ Could not fetch zones from Cloudflare.{RESET_COLOR}")
        return

    record_name = None
    try:
        cf_api = CloudflareAPI(acc["api_token"])
        zone_id = zone["zone_id"]
        logger.info(f"Fetching records for zone {zone['domain']}...")
        records_from_cf = list(cf_api.list_dns_records(zone_id))
        
        if records_from_cf:
            print_fast(f"\n{COLOR_TITLE}--- Existing Records ---{RESET_COLOR}")
            for i, cf_record in enumerate(records_from_cf):
                print_fast(f"{i+1}. {cf_record.name} (Type: {cf_record.type}, Content: {cf_record.content})")
            print_fast(f"{len(records_from_cf)+1}. Enter a new record name manually")
            print_fast("-------------------------")
            
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
                        print_fast(f"{COLOR_ERROR}❌ Invalid choice.{RESET_COLOR}")
                except ValueError:
                    print_fast(f"{COLOR_ERROR}❌ Invalid input. Please enter a number.{RESET_COLOR}")
        else:
            logger.info(f"No existing records found in Cloudflare for zone {zone['domain']}. Proceeding with manual entry.")

    except APIError as e:
        logger.error(f"Cloudflare API Error fetching records: {e}")
        print_fast(f"{COLOR_WARNING}⚠️ Proceeding with manual record name entry.{RESET_COLOR}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print_fast(f"{COLOR_WARNING}⚠️ Proceeding with manual record name entry.{RESET_COLOR}")

    if not record_name:
        record_name = get_validated_input(
            "Record name (e.g., vpn.example.com): ",
            is_valid_record_name,
            "Invalid record name."
        )

    if find_record(zone, record_name):
        logger.warning(f"Record '{record_name}' already exists locally.")
        print_fast(f"{COLOR_INFO}ℹ️ To update, please delete and re-add it.{RESET_COLOR}")
        return

    rec_type = get_record_type()
    ip_list = get_ip_list(rec_type)
    
    schedule = get_schedule_config()
    if not schedule:
        print_fast(f"{COLOR_WARNING}Rotation schedule setup cancelled. Record not added.{RESET_COLOR}")
        return

    # The last argument is now the schedule object
    add_record_to_config(acc['name'], zone['domain'], record_name, rec_type, ip_list, schedule)
    logger.info(f"Record '{record_name}' added to zone '{zone['domain']}'.")

def list_records_from_config():
    """
    Lists all single-record rotation configurations in a table.
    """
    data = load_config()
    if not any(acc.get("zones") for acc in data["accounts"]):
        logger.info("No records to display.")
        print_fast("No records configured for rotation. Please add a record first.")
        return

    print_fast(f"\n{COLOR_TITLE}--- Records Configured for Rotation ---{RESET_COLOR}")
    
    all_records_data = []
    triggers = data.get("triggers", [])
    
    def get_trigger_name(trigger_id):
        for t in triggers:
            if t["id"] == trigger_id:
                return t["name"]
        return "Unknown Trigger"

    for acc in data["accounts"]:
        for zone in acc.get("zones", []):
            for record in zone.get("records", []):
                schedule_info = "Not Set"
                schedule = record.get("schedule")
                if schedule:
                    if schedule.get("type") == "time":
                        schedule_info = f"Time: {schedule.get('interval_minutes', 'N/A')} min"
                    elif schedule.get("type") == "trigger":
                        trigger_name = get_trigger_name(schedule.get("trigger_id"))
                        schedule_info = f"Trigger: {trigger_name}"

                all_records_data.append({
                    "Account": acc["name"],
                    "Zone": zone["domain"],
                    "Record": record["name"],
                    "Type": record["type"],
                    "IPs": summarize_list(record.get("ips", [])),
                    "Schedule": schedule_info
                })

    if all_records_data:
        headers = {
            "Account": "Account",
            "Zone": "Zone",
            "Record": "Record",
            "Type": "Type",
            "IPs": "IPs",
            "Schedule": "Schedule"
        }
        display_as_table(all_records_data, headers)
    else:
        print_fast("No records configured for rotation.")


def delete_record():
    """
    Guides the user through deleting a single-record rotation configuration.
    """
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
        print_fast(f"{COLOR_ERROR}❌ No accounts available.{RESET_COLOR}")
        return

    acc = select_from_list(data["accounts"], "Select an account to delete a record from:")
    if not acc:
        return

    if not acc["zones"]:
        logger.warning(f"No zones available in account '{acc['name']}'.")
        print_fast(f"{COLOR_ERROR}❌ No zones available in account '{acc['name']}'.{RESET_COLOR}")
        return

    zone = select_from_list(acc["zones"], f"Select a zone in '{acc['name']}' to delete a record from:")
    if not zone:
        return

    if not zone["records"]:
        logger.warning(f"No records available in zone '{zone['domain']}'.")
        print_fast(f"{COLOR_ERROR}❌ No records available in zone '{zone['domain']}'.{RESET_COLOR}")
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
    """
    Guides the user through editing a single-record rotation configuration.
    """
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
        print_fast(f"{COLOR_ERROR}❌ No accounts available.{RESET_COLOR}")
        return

    acc = select_from_list(data["accounts"], "Select an account to edit a record in:")
    if not acc:
        return

    if not acc["zones"]:
        logger.warning(f"No zones available in account '{acc['name']}'.")
        print_fast(f"{COLOR_ERROR}❌ No zones available in account '{acc['name']}'.{RESET_COLOR}")
        return

    zone = select_from_list(acc["zones"], f"Select a zone in '{acc['name']}' to edit a record in:")
    if not zone:
        return

    if not zone["records"]:
        logger.warning(f"No records available in zone '{zone['domain']}'.")
        print_fast(f"{COLOR_ERROR}❌ No records available in zone '{zone['domain']}'.{RESET_COLOR}")
        return

    record_to_edit = select_from_list(zone["records"], f"Select a record in '{zone['domain']}' to edit:")
    if not record_to_edit:
        return

    print_fast(f"\n{COLOR_TITLE}--- Editing Record: {record_to_edit['name']} ---{RESET_COLOR}")
    print_fast(f"Current IPs: {', '.join(record_to_edit['ips'])}")
    new_ips_str = input(f"Enter new IPs (comma separated) or press Enter to keep current: ").strip()
    new_ips = [ip.strip() for ip in new_ips_str.split(',')] if new_ips_str else None

    print_fast(f"Current Type: {record_to_edit['type']}")
    new_type = input(f"Enter new type (A/CNAME) or press Enter to keep current: ").strip().upper() or None

    current_interval = record_to_edit.get('rotation_interval_minutes', 'Default (30)')
    print_fast(f"Current Rotation Interval (minutes): {current_interval}")
    new_interval_str = input(f"Enter new interval (minutes, min 5, or 'none' to use default) or press Enter to keep current: ").strip()
    
    edit_record_in_config(acc['name'], zone['domain'], record_to_edit['name'], new_ips, new_type, new_interval_str)
    logger.info(f"Record '{record_to_edit['name']}' in zone '{zone['domain']}' updated.")


def rotate_based_on_list_of_ips_single_record_menu():
    """
    Displays the submenu for managing single-record IP rotations.
    """
    while True:
        clear_screen()
        print_fast(f"\n{COLOR_TITLE}--- Rotate Based on a List of IPs (Single-Record) ---{RESET_COLOR}")
        list_records_from_config()
        print_slow("\n1. 📝 Create DNS Rotation")
        print_slow("2. ✏️ Edit an Existing DNS Rotation")
        print_slow("3. 🗑️ Delete a DNS Rotation")
        print_slow("4. 📄 View logs")
        print_slow("0. ⬅️ Return to previous menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

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
                print_fast(f"{COLOR_WARNING}No records configured for rotation. Please add a record first.{RESET_COLOR}")
                input("\nPress Enter to return...")
                continue
            
            records = []
            for acc in data["accounts"]:
                for zone in acc.get("zones", []):
                    for record in zone.get("records", []):
                        records.append(record)

            if not records:
                print_fast(f"{COLOR_WARNING}No records configured for rotation. Please add a record first.{RESET_COLOR}")
                input("\nPress Enter to return...")
                continue

            record_to_view = select_from_list(records, "Select a record to view logs for:")
            if record_to_view:
                view_live_logs(record_name=record_to_view['name'])
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
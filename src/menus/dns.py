"""
DNS Record Management Menu.

This module provides the user interface for managing DNS records directly
through the Cloudflare API. It allows users to select an account and a zone,
and then perform operations such as listing, adding, editing, and deleting
DNS records.
"""
from ..config import load_config
from ..cloudflare_api import CloudflareAPI
from ..input_helper import get_validated_input
from ..validator import is_valid_dns_record_type
from ..logger import logger
from ..display import *
from ..error_handler import MissingPermissionError
from cloudflare import APIError
from .utils import clear_screen, select_from_list, confirm_action, parse_selection

def dns_management_menu():
    """
    Displays the main menu for DNS management.
    """
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
        print_fast(f"{COLOR_ERROR}❌ No accounts available. Please add an account first.{RESET_COLOR}")
        input("\nPress Enter to return...")
        return

    acc = None
    if len(data["accounts"]) == 1:
        acc = data["accounts"][0]
        logger.info(f"Auto-selecting the only account: {acc['name']}")
    else:
        acc = select_from_list(data["accounts"], "Select an account:")
    
    if not acc:
        return

    cf_api = CloudflareAPI(acc["api_token"])

    try:
        print_fast("Fetching zones...")
        zones_from_cf = list(cf_api.list_zones())
    except APIError as e:
        logger.error(f"Cloudflare API Error fetching zones for account '{acc['name']}': {e}")
        print_fast(f"{COLOR_ERROR}❌ Error fetching zones: {e}{RESET_COLOR}")
        input("\nPress Enter to return...")
        return

    if not zones_from_cf:
        print_fast(f"{COLOR_WARNING}\nNo zones found for this account in Cloudflare.{RESET_COLOR}")
        input("\nPress Enter to return...")
        return

    zones_for_display = [{"#": i + 1, "Domain": zone.name} for i, zone in enumerate(zones_from_cf)]
    
    while True:
        clear_screen()
        print_fast(f"{COLOR_TITLE}--- (DNS Management) for Account: {acc['name']} ---{RESET_COLOR}")
        print_fast("\n--- Available Zones ---")
        display_as_table(zones_for_display, headers="keys")
        
        try:
            selection = input("Enter the # of the zone to manage DNS records for (or 0 to go back): ")
            if selection == '0':
                break
            
            selection = int(selection)
            if 1 <= selection <= len(zones_from_cf):
                selected_zone = zones_from_cf[selection - 1]
                manage_zone_records(cf_api, selected_zone.id, selected_zone.name)
            else:
                print_fast(f"{COLOR_ERROR}❌ Invalid selection.{RESET_COLOR}")
                input("\nPress Enter to continue...")
        except ValueError:
            print_fast(f"{COLOR_ERROR}❌ Invalid input. Please enter a number.{RESET_COLOR}")
            input("\nPress Enter to continue...")

def manage_zone_records(cf_api, zone_id, zone_name):
    """
    Displays and handles the DNS record management options for a specific zone.

    This function lists all DNS records for the given zone and provides options
    to add, edit, or delete records.

    Args:
        cf_api (CloudflareAPI): An instance of the CloudflareAPI client.
        zone_id (str): The ID of the zone to manage.
        zone_name (str): The name of the zone.
    """
    while True:
        clear_screen()
        print_fast(f"{COLOR_TITLE}--- DNS Records for {zone_name} ---{RESET_COLOR}")
        try:
            records = list(cf_api.list_dns_records(zone_id))
            if not records:
                print_fast(f"{COLOR_WARNING}\nNo DNS records found for this zone.{RESET_COLOR}")
            else:
                records_for_display = []
                for i, record in enumerate(records):
                    records_for_display.append({
                        "#": i + 1,
                        "Type": record.type,
                        "Name": record.name,
                        "Content": record.content,
                        "TTL": record.ttl,
                        "Proxied": "Yes" if record.proxied else "No"
                    })
                display_as_table(records_for_display, headers="keys")

            print_fast(f"\n{COLOR_TITLE}Choose an option:{RESET_COLOR}")
            print_slow("1) Add a new DNS record")
            print_slow("2) Edit an existing DNS record")
            print_slow("3) Delete a DNS record")
            print_slow("0) Back to zone selection")
            print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

            choice = input("👉 Enter your choice: ").strip()

            if choice == "1":
                add_dns_record(cf_api, zone_id, zone_name)
            elif choice == "2":
                if records:
                    edit_dns_record(cf_api, zone_id, zone_name, records)
                else:
                    print_fast(f"{COLOR_WARNING}No records to edit.{RESET_COLOR}")
                    input("\nPress Enter to continue...")
            elif choice == "3":
                if records:
                    delete_dns_record(cf_api, zone_id, zone_name, records)
                else:
                    print_fast(f"{COLOR_WARNING}No records to delete.{RESET_COLOR}")
                    input("\nPress Enter to continue...")
            elif choice == "0":
                break
            else:
                print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
                input("\nPress Enter to continue...")

        except APIError as e:
            logger.error(f"Error fetching DNS records for zone {zone_name}: {e}")
            print_fast(f"{COLOR_ERROR}❌ An API error occurred: {e}{RESET_COLOR}")
            input("\nPress Enter to return...")
            return
        except Exception as e:
            logger.error(f"An unexpected error occurred in manage_zone_records: {e}", exc_info=True)
            print_fast(f"{COLOR_ERROR}❌ An unexpected error occurred: {e}{RESET_COLOR}")
            input("\nPress Enter to return...")
            return

def add_dns_record(cf_api, zone_id, zone_name):
    """
    Handles the user input and API call for adding a new DNS record.

    Args:
        cf_api (CloudflareAPI): An instance of the CloudflareAPI client.
        zone_id (str): The ID of the zone where the record will be added.
        zone_name (str): The name of the zone (for logging purposes).
    """
    print_fast(f"\n{COLOR_TITLE}--- Add New DNS Record ---{RESET_COLOR}")
    
    record_type = get_validated_input(
        "Enter record type (A, AAAA, CNAME, TXT, MX, etc.): ",
        is_valid_dns_record_type,
        "Invalid record type."
    ).upper()

    name = get_validated_input(
        "Enter record name (e.g., www, @, mail): ",
        lambda n: n is not None,
        "Name cannot be empty."
    )

    content = get_validated_input(
        "Enter record content (IP address, domain, etc.): ",
        lambda c: c is not None,
        "Content cannot be empty."
    )

    ttl_str = input("Enter TTL (or press Enter for default): ").strip()
    ttl = int(ttl_str) if ttl_str.isdigit() else None

    proxied_str = get_validated_input(
        "Enable Cloudflare Proxy? (yes/no): ",
        lambda p: p.lower() in ['yes', 'no'],
        "Please enter 'yes' or 'no'."
    ).lower()
    proxied = proxied_str == 'yes'

    try:
        print_fast("Creating DNS record...")
        cf_api.create_dns_record(zone_id, name, record_type, content, proxied, ttl)
        print_fast(f"{COLOR_SUCCESS}✅ DNS record created successfully!{RESET_COLOR}")
    except APIError as e:
        logger.error(f"Failed to create DNS record in zone {zone_name}: {e}")
        print_fast(f"{COLOR_ERROR}❌ Error creating DNS record: {e}{RESET_COLOR}")
    
    input("\nPress Enter to continue...")

def edit_dns_record(cf_api, zone_id, zone_name, records):
    """
    Handles the user input and API call for editing an existing DNS record.

    Args:
        cf_api (CloudflareAPI): An instance of the CloudflareAPI client.
        zone_id (str): The ID of the zone containing the record.
        zone_name (str): The name of the zone (for logging purposes).
        records (list): The list of current DNS records in the zone.
    """
    print_fast(f"\n{COLOR_TITLE}--- Edit DNS Record ---{RESET_COLOR}")
    try:
        selection = int(input("Enter the # of the record to edit: "))
        if not (1 <= selection <= len(records)):
            print_fast(f"{COLOR_ERROR}❌ Invalid selection.{RESET_COLOR}")
            return

        record_to_edit = records[selection - 1]

        print_fast(f"\nEditing record: {record_to_edit.name} ({record_to_edit.type})")
        print_fast(f"Current content: {record_to_edit.content}")
        print_fast("Leave fields blank to keep existing values.")

        new_name = input(f"New name (current: {record_to_edit.name}): ").strip() or record_to_edit.name
        new_type = get_validated_input(
            f"New type (current: {record_to_edit.type}): ",
            lambda t: is_valid_dns_record_type(t) if t else True,
            "Invalid record type."
        ).upper() or record_to_edit.type
        new_content = input(f"New content (current: {record_to_edit.content}): ").strip() or record_to_edit.content
        
        new_ttl_str = input(f"New TTL (current: {record_to_edit.ttl}): ").strip()
        new_ttl = int(new_ttl_str) if new_ttl_str.isdigit() else record_to_edit.ttl

        current_proxied_status = 'yes' if record_to_edit.proxied else 'no'
        new_proxied_str = get_validated_input(
            f"Enable Cloudflare Proxy? (current: {current_proxied_status}) (yes/no): ",
            lambda p: p.lower() in ['yes', 'no', ''],
            "Please enter 'yes' or 'no'."
        ).lower()
        new_proxied = {'yes': True, 'no': False, '': record_to_edit.proxied}[new_proxied_str]

        print_fast("Updating DNS record...")
        cf_api.update_dns_record(
            zone_id,
            record_to_edit.id,
            new_name,
            new_type,
            new_content,
            new_proxied,
            new_ttl
        )
        print_fast(f"{COLOR_SUCCESS}✅ DNS record updated successfully!{RESET_COLOR}")

    except ValueError:
        print_fast(f"{COLOR_ERROR}❌ Invalid input. Please enter a number.{RESET_COLOR}")
    except APIError as e:
        logger.error(f"Failed to update DNS record in zone {zone_name}: {e}")
        print_fast(f"{COLOR_ERROR}❌ Error updating DNS record: {e}{RESET_COLOR}")
    
    input("\nPress Enter to continue...")

def delete_dns_record(cf_api, zone_id, zone_name, records):
    """
    Handles the user input and API call for deleting one or more DNS records.

    Args:
        cf_api (CloudflareAPI): An instance of the CloudflareAPI client.
        zone_id (str): The ID of the zone containing the records.
        zone_name (str): The name of the zone (for logging purposes).
        records (list): The list of current DNS records in the zone.
    """
    print_fast(f"\n{COLOR_TITLE}--- Delete DNS Records ---{RESET_COLOR}")
    selection_str = input("Enter the # of the record(s) to delete (e.g., 1, 2-4, 5): ")

    try:
        indices_to_delete = parse_selection(selection_str, len(records))
        if not indices_to_delete:
            print_fast(f"{COLOR_WARNING}No valid records selected.{RESET_COLOR}")
            input("\nPress Enter to continue...")
            return

        records_to_delete = [records[i] for i in indices_to_delete]
        
        if len(records_to_delete) == 1:
            record_to_delete = records_to_delete[0]
            print_fast(f"\n{COLOR_WARNING}⚠️  You are about to delete the record: {record_to_delete.name} ({record_to_delete.type}){RESET_COLOR}")
            confirmation = input(f"To confirm, please type the record name '{record_to_delete.name}': ")
            if confirmation.strip().lower() != record_to_delete.name.lower():
                print_fast(f"{COLOR_ERROR}❌ Deletion cancelled. The entered name did not match.{RESET_COLOR}")
                input("\nPress Enter to continue...")
                return
        else:
            print_fast(f"\n{COLOR_WARNING}⚠️  You are about to delete the following records:{RESET_COLOR}")
            for i, record in enumerate(records_to_delete):
                 print_fast(f"{i+1}. {record.name} ({record.type}) - {record.content}")
            
            confirmation = input("To confirm, please type 'delete': ")
            if confirmation.strip().lower() != 'delete':
                print_fast(f"{COLOR_ERROR}❌ Deletion cancelled.{RESET_COLOR}")
                input("\nPress Enter to continue...")
                return

        deleted_count = 0
        failed_count = 0
        print_fast("")
        for record in records_to_delete:
            try:
                print_fast(f"Deleting record {record.name}...")
                cf_api.delete_dns_record(zone_id, record.id)
                logger.info(f"DNS record '{record.name}' deleted successfully from zone '{zone_name}'.")
                deleted_count += 1
            except APIError as e:
                logger.error(f"Failed to delete DNS record {record.name} in zone {zone_name}: {e}")
                print_fast(f"{COLOR_ERROR}❌ Error deleting record {record.name}: {e}{RESET_COLOR}")
                failed_count += 1
        
        print_fast(f"\n{COLOR_TITLE}--- Deletion Summary ---{RESET_COLOR}")
        if deleted_count > 0:
            print_fast(f"{COLOR_SUCCESS}✅ Successfully deleted {deleted_count} record(s).{RESET_COLOR}")
        if failed_count > 0:
            print_fast(f"{COLOR_ERROR}❌ Failed to delete {failed_count} record(s).{RESET_COLOR}")

    except ValueError as e:
        print_fast(f"{COLOR_ERROR}❌ Invalid input: {e}{RESET_COLOR}")
    
    input("\nPress Enter to continue...")
"""
DNS Record Management Menu.

This module provides the user interface for managing DNS records directly
through the Cloudflare API. It allows users to select an account and a zone,
and then perform operations such as listing, adding, editing, and deleting
DNS records.
"""
from ..core import accounts as core_accounts
from ..core import zones as core_zones
from ..core import dns as core_dns
from .utils import get_validated_input
from ..core.validator import is_valid_dns_record_type
from ..core.logger import logger
from ..display import (
    display_as_table,
    print_fast,
    print_slow,
    COLOR_TITLE,
    COLOR_SUCCESS,
    COLOR_ERROR,
    COLOR_WARNING,
    COLOR_SEPARATOR,
    OPTION_SEPARATOR,
    RESET_COLOR,
)
from ..core.exceptions import APIError, AuthenticationError
from .utils import clear_screen, select_from_list, confirm_action, parse_selection

def dns_management_menu():
    """
    Displays the main menu for DNS management.
    """
    accounts = core_accounts.get_accounts()
    if not accounts:
        logger.warning("No accounts available.")
        print_fast(f"{COLOR_ERROR}❌ No accounts available. Please add an account first.{RESET_COLOR}")
        input("\nPress Enter to return...")
        return

    acc = None
    if len(accounts) == 1:
        acc = accounts[0]
        logger.info(f"Auto-selecting the only account: {acc['name']}")
    else:
        acc = select_from_list(accounts, "Select an account:")
    
    if not acc:
        return

    api_token = acc["api_token"]

    try:
        print_fast("Fetching zones...")
        zones_from_cf = core_zones.list_zones(api_token)
    except (APIError, AuthenticationError) as e:
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
                manage_zone_records_menu(api_token, selected_zone.id, selected_zone.name)
            else:
                print_fast(f"{COLOR_ERROR}❌ Invalid selection.{RESET_COLOR}")
                input("\nPress Enter to continue...")
        except ValueError:
            print_fast(f"{COLOR_ERROR}❌ Invalid input. Please enter a number.{RESET_COLOR}")
            input("\nPress Enter to continue...")

def manage_zone_records_menu(api_token, zone_id, zone_name):
    """
    Displays and handles the DNS record management options for a specific zone.
    """
    while True:
        clear_screen()
        print_fast(f"{COLOR_TITLE}--- DNS Records for {zone_name} ---{RESET_COLOR}")
        try:
            records = core_dns.list_dns_records(api_token, zone_id)
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
                add_dns_record_menu(api_token, zone_id, zone_name)
            elif choice == "2":
                if records:
                    edit_dns_record_menu(api_token, zone_id, zone_name, records)
                else:
                    print_fast(f"{COLOR_WARNING}No records to edit.{RESET_COLOR}")
                    input("\nPress Enter to continue...")
            elif choice == "3":
                if records:
                    delete_dns_record_menu(api_token, zone_id, zone_name, records)
                else:
                    print_fast(f"{COLOR_WARNING}No records to delete.{RESET_COLOR}")
                    input("\nPress Enter to continue...")
            elif choice == "0":
                break
            else:
                print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
                input("\nPress Enter to continue...")

        except (APIError, AuthenticationError) as e:
            logger.error(f"Error fetching DNS records for zone {zone_name}: {e}")
            print_fast(f"{COLOR_ERROR}❌ An API error occurred: {e}{RESET_COLOR}")
            input("\nPress Enter to return...")
            return
        except Exception as e:
            logger.error(f"An unexpected error occurred in manage_zone_records: {e}", exc_info=True)
            print_fast(f"{COLOR_ERROR}❌ An unexpected error occurred: {e}{RESET_COLOR}")
            input("\nPress Enter to return...")
            return

def add_dns_record_menu(api_token, zone_id, zone_name):
    """
    Handles the user input and API call for adding a new DNS record.
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
        core_dns.create_dns_record(api_token, zone_id, name, record_type, content, proxied, ttl)
        print_fast(f"{COLOR_SUCCESS}✅ DNS record created successfully!{RESET_COLOR}")
    except (APIError, AuthenticationError) as e:
        logger.error(f"Failed to create DNS record in zone {zone_name}: {e}")
        print_fast(f"{COLOR_ERROR}❌ Error creating DNS record: {e}{RESET_COLOR}")
    
    input("\nPress Enter to continue...")

def edit_dns_record_menu(api_token, zone_id, zone_name, records):
    """
    Handles the user input and API call for editing an existing DNS record.
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
        core_dns.update_dns_record(
            api_token,
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
    except (APIError, AuthenticationError) as e:
        logger.error(f"Failed to update DNS record in zone {zone_name}: {e}")
        print_fast(f"{COLOR_ERROR}❌ Error updating DNS record: {e}{RESET_COLOR}")
    
    input("\nPress Enter to continue...")

def delete_dns_record_menu(api_token, zone_id, zone_name, records):
    """
    Handles the user input and API call for deleting one or more DNS records.
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
                core_dns.delete_dns_record(api_token, zone_id, record.id)
                logger.info(f"DNS record '{record.name}' deleted successfully from zone '{zone_name}'.")
                deleted_count += 1
            except (APIError, AuthenticationError) as e:
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
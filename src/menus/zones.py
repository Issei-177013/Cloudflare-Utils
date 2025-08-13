"""
Zone Management Menu.

This module provides the user interface for managing Cloudflare zones.
It allows users to list, add, view details of, delete, and modify the
settings of their zones.
"""
from ..config import load_config, find_zone
from ..cloudflare_api import CloudflareAPI
from ..input_helper import get_validated_input, get_zone_type
from ..validator import is_valid_domain
from ..logger import logger
from ..display import display_as_table
from ..error_handler import MissingPermissionError
from cloudflare import APIError
from .utils import clear_screen, select_from_list

def edit_zone_settings(cf_api, zone_id, zone_name):
    """
    Manages the editing of core settings for a specific zone.

    This function displays the current values of key settings (SSL, HTTPS, etc.)
    and allows the user to update them one by one.

    Args:
        cf_api (CloudflareAPI): An instance of the CloudflareAPI client.
        zone_id (str): The ID of the zone to edit.
        zone_name (str): The name of the zone.
    """
    while True:
        try:
            print(f"\n--- Current settings for {zone_name} ---")
            settings = cf_api.get_zone_core_settings(zone_id)

            settings_data = [
                {"Setting": "SSL/TLS Mode", "Value": settings.get('ssl', 'N/A')},
                {"Setting": "Always Use HTTPS", "Value": settings.get('always_use_https', 'N/A')},
                {"Setting": "Automatic HTTPS Rewrites", "Value": settings.get('automatic_https_rewrites', 'N/A')},
                {"Setting": "Minimum TLS Version", "Value": settings.get('min_tls_version', 'N/A')}
            ]
            display_as_table(settings_data, headers="keys")

            print("\nWhich setting do you want to update?")
            print("1) SSL/TLS Mode")
            print("2) Always Use HTTPS")
            print("3) Automatic HTTPS Rewrites")
            print("4) Minimum TLS Version")
            print("0) Cancel")
            
            choice = input("👉 Enter choice: ").strip()

            if choice == '0':
                break
            elif choice not in ['1', '2', '3', '4']:
                print("❌ Invalid choice.")
                continue

            setting_map = {
                '1': {'name': 'ssl', 'prompt': "Enter new value (off, flexible, full, full_strict): ", 'valid_values': ['off', 'flexible', 'full', 'full_strict']},
                '2': {'name': 'always_use_https', 'prompt': "Enter new value (on/off): ", 'valid_values': ['on', 'off']},
                '3': {'name': 'automatic_https_rewrites', 'prompt': "Enter new value (on/off): ", 'valid_values': ['on', 'off']},
                '4': {'name': 'min_tls_version', 'prompt': "Enter new value (1.0, 1.1, 1.2, 1.3): ", 'valid_values': ['1.0', '1.1', '1.2', '1.3']}
            }
            
            setting_to_update = setting_map[choice]
            setting_name = setting_to_update['name']
            prompt_text = setting_to_update['prompt']
            valid_values = setting_to_update['valid_values']

            new_value = get_validated_input(
                prompt_text,
                lambda v: v.lower() in valid_values,
                f"Invalid value. Please choose from: {', '.join(valid_values)}"
            ).lower()

            try:
                print(f"Updating '{setting_name}' to '{new_value}'...")
                cf_api.update_zone_setting(zone_id, setting_name, new_value)
                print(f"✅ Setting '{setting_name}' updated successfully to '{new_value}'.")
            except (APIError, MissingPermissionError) as e:
                logger.error(f"Failed to update setting '{setting_name}' for zone {zone_name}: {e}")
                if "Missing permission: 'Zone Settings:Edit'" in str(e):
                    print("❌ Missing permission: 'Zone Settings:Edit'")
                else:
                    print(f"❌ API Error: {e}")
                break

        except (APIError, MissingPermissionError) as e:
            logger.error(f"Error managing zone settings for {zone_name}: {e}")
            if "Missing permission: 'Zone Settings:Edit'" in str(e):
                 print("❌ Missing permission: 'Zone Settings:Edit'")
            else:
                print(f"❌ An API error occurred: {e}")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred in edit_zone_settings: {e}", exc_info=True)
            print(f"❌ An unexpected error occurred: {e}")
            break


def zone_management_menu():
    """
    Displays the main menu for Zone Management.

    This function handles the user flow for selecting an account, listing its zones,
    and navigating to various zone operations like adding, viewing, deleting, or
    editing settings for a zone.
    """
    data = load_config()
    if not data["accounts"]:
        logger.warning("No accounts available.")
        print("❌ No accounts available. Please add an account first.")
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

    while True:
        clear_screen()
        print(f"--- (Zone Management) for Account: {acc['name']} ---")

        try:
            print("Fetching zones...")
            zones_from_cf = list(cf_api.list_zones())
            
            if not zones_from_cf:
                print("\nNo zones found for this account in Cloudflare.")
            else:
                zones_for_display = []
                for i, zone in enumerate(zones_from_cf):
                    zones_for_display.append({
                        "id_short": i + 1,
                        "domain": zone.name,
                        "status": zone.status,
                        "id_full": zone.id
                    })
                
                print("\n--- Available Zones ---")
                headers = {
                    "id_short": "#",
                    "domain": "Domain Name",
                    "status": "Status",
                    "id_full": "Zone ID"
                }
                display_as_table(zones_for_display, headers=headers)

        except APIError as e:
            logger.error(f"Cloudflare API Error fetching zones for account '{acc['name']}': {e}")
            print(f"❌ Error fetching zones: {e}")
            input("\nPress Enter to return...")
            return

        print("\nChoose an option:")
        print("1) Add a new zone")
        print("2) View zone info")
        print("3) Delete a zone")
        print("4) Edit Zone Settings")
        print("0) Back to main menu")
        print("--------------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            domain_name = get_validated_input("Enter the domain name to add: ", is_valid_domain, "Invalid domain name.")
            if domain_name:
                zone_type = get_zone_type()
                try:
                    print(f"Adding zone {domain_name}...")
                    new_zone = cf_api.add_zone(domain_name, zone_type=zone_type)
                    zone_details = cf_api.get_zone_details(new_zone["id"])

                    print(f"\n✅ Zone '{domain_name}' added successfully!")
                    print(f"   - Status: {zone_details.status}")
                    print(f"   - ID: {zone_details.id}")

                    if zone_details.name_servers:
                        print("\n📢 Please update your domain's nameservers at your registrar to:")
                        for ns in zone_details.name_servers:
                            print(f"     - {ns}")
                    else:
                        print("⚠️ No nameservers returned by Cloudflare. Please check manually.")

                    if zone_details.status.lower() == "pending":
                        print("\n⚠️ Status: Pending")
                        print("⏳ Your domain is not yet active on Cloudflare.")
                        print("❗ If nameservers are not updated within the grace period, this zone may be deleted.")

                except (MissingPermissionError, RuntimeError) as e:
                    logger.error(f"Failed to add zone '{domain_name}': {e}")
                    print(f"\n❌ Error adding zone: {e}")
                    
                input("\nPress Enter to continue...")

        elif choice == "2":
            if not zones_from_cf:
                print("No zones to view.")
            else:
                try:
                    selection = int(input("Enter the # of the zone to view: "))
                    if 1 <= selection <= len(zones_from_cf):
                        selected_zone_id = zones_from_cf[selection - 1].id
                        print(f"Fetching details for zone {selected_zone_id}...")
                        zone_details = cf_api.get_zone_details(selected_zone_id)
                        
                        print("\n--- Zone Details ---")
                        details = {
                            "Domain": zone_details.name,
                            "ID": zone_details.id,
                            "Status": zone_details.status,
                            "Plan": zone_details.plan.name,
                            "Created On": zone_details.created_on.strftime('%Y-%m-%d'),
                            "Nameservers": ", ".join(zone_details.name_servers)
                        }
                        display_as_table([details], headers="keys")

                    else:
                        print("❌ Invalid selection.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
                except APIError as e:
                    logger.error(f"Failed to fetch zone details: {e}")
                    print(f"❌ Error fetching zone details: {e}")
            input("\nPress Enter to continue...")

        elif choice == "3":
            if not zones_from_cf:
                print("No zones to delete.")
            else:
                try:
                    selection = int(input("Enter the # of the zone to delete: "))
                    if 1 <= selection <= len(zones_from_cf):
                        zone_to_delete = zones_from_cf[selection - 1]
                        
                        print(f"\n⚠️ You are about to delete the zone '{zone_to_delete.name}'.")
                        print("This action is irreversible.")
                        
                        confirmation = input(f"To confirm, please type the domain name '{zone_to_delete.name}': ")
                        
                        if confirmation.strip().lower() == zone_to_delete.name.lower():
                            try:
                                print(f"Deleting zone {zone_to_delete.name}...")
                                cf_api.delete_zone(zone_to_delete.id)
                                logger.info(f"Zone '{zone_to_delete.name}' deleted successfully.")
                                print(f"✅ Zone '{zone_to_delete.name}' has been deleted.")
                            except APIError as e:
                                logger.error(f"Failed to delete zone '{zone_to_delete.name}': {e}")
                                print(f"❌ Error deleting zone: {e}")
                        else:
                            print("❌ Deletion cancelled. The entered name did not match.")
                    else:
                        print("❌ Invalid selection.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
            input("\nPress Enter to continue...")

        elif choice == "4":
            if not zones_from_cf:
                print("No zones to edit.")
            else:
                try:
                    selection = int(input("Enter the # of the zone to edit settings for: "))
                    if 1 <= selection <= len(zones_from_cf):
                        selected_zone = zones_from_cf[selection - 1]
                        edit_zone_settings(cf_api, selected_zone.id, selected_zone.name)
                    else:
                        print("❌ Invalid selection.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
            input("\nPress Enter to continue...")
            
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice in zone menu: {choice}")
            print("❌ Invalid choice. Please select a valid option.")
            input("\nPress Enter to continue...")
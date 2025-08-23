"""
Telegram Bot Settings Menu.

This module provides the user interface for managing the Telegram bot settings.
"""
import csv
import os
from .utils import clear_screen, get_user_input, get_numeric_input, confirm_action, _get_sanitized_input
from ..core.config import config_manager
from ..core.service_manager import service_manager, SYSTEMD_PATH, SERVICE_FILE_NAME
from ..display import *
from ..core.logger import logger

def manage_systemd_install_menu():
    """Menu for installing or uninstalling the systemd service."""
    clear_screen()
    print_fast(f"{COLOR_TITLE}\n--- Install/Uninstall systemd Service ---{RESET_COLOR}")
    print_fast("This action requires root permissions and will interact with /etc/systemd/system/.")
    
    dest_path = os.path.join(SYSTEMD_PATH, SERVICE_FILE_NAME)
    is_installed = os.path.exists(dest_path)

    if is_installed:
        print_fast(f"\n{COLOR_WARNING}Service appears to be installed.{RESET_COLOR}")
        if confirm_action("Do you want to uninstall the service?"):
            success, message = service_manager.uninstall_service()
            if success:
                print_fast(f"{COLOR_SUCCESS}✅ {message}{RESET_COLOR}")
            else:
                print_fast(f"{COLOR_ERROR}❌ {message}{RESET_COLOR}")
    else:
        print_fast(f"\n{COLOR_INFO}Service does not appear to be installed.{RESET_COLOR}")
        if confirm_action("Do you want to install the service?"):
            success, message = service_manager.install_service()
            if success:
                print_fast(f"{COLOR_SUCCESS}✅ {message}{RESET_COLOR}")
                print_fast(f"{COLOR_INFO}ℹ️ The service is now installed and enabled to start on boot.{RESET_COLOR}")
            else:
                print_fast(f"{COLOR_ERROR}❌ {message}{RESET_COLOR}")

    input("\nPress Enter to return...")

def manage_service_menu():
    """
    Displays and handles the menu for managing the bot service.
    """
    bot_config = config_manager.get_config().get("bot", {})
    if not bot_config.get("enabled"):
        clear_screen()
        print_fast(f"{COLOR_WARNING}\nBot is disabled in settings. Cannot manage service.{RESET_COLOR}")
        print_fast("Please enable the bot first from the Telegram Bot Settings menu.")
        input("\nPress Enter to continue...")
        return

    while True:
        clear_screen()
        status = service_manager.get_status()
        print_fast(f"{COLOR_TITLE}\n--- Manage Service ---{RESET_COLOR}")
        print_fast(f"Service Status: {status}")
        print_fast(f"Mode: {'systemd' if service_manager.systemd_available else 'background process'}")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        if service_manager.systemd_available:
            print_fast("1. Start Service")
            print_fast("2. Stop Service")
            print_fast("3. Restart Service")
            print_fast("4. Install/Uninstall Service")
            print_fast("0. Back")
        else: # Fallback mode
            print_fast("1. Start Service")
            print_fast("2. Stop Service")
            print_fast("0. Back")
        
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")
        choice = input("👉 Enter your choice: ").strip()

        if choice == '0':
            break

        if choice == '1':
            success, message = service_manager.start_service()
            if success:
                print_fast(f"{COLOR_SUCCESS}✅ Service started successfully.{RESET_COLOR}")
            else:
                print_fast(f"{COLOR_ERROR}❌ {message}{RESET_COLOR}")
            input("\nPress Enter to continue...")
        elif choice == '2':
            success, message = service_manager.stop_service()
            if success:
                print_fast(f"{COLOR_SUCCESS}✅ Service stopped successfully.{RESET_COLOR}")
            else:
                print_fast(f"{COLOR_ERROR}❌ {message}{RESET_COLOR}")
            input("\nPress Enter to continue...")
        
        elif service_manager.systemd_available and choice == '3':
            success, message = service_manager.restart_service()
            if success:
                print_fast(f"{COLOR_SUCCESS}✅ Service restarted successfully.{RESET_COLOR}")
            else:
                print_fast(f"{COLOR_ERROR}❌ {message}{RESET_COLOR}")
            input("\nPress Enter to continue...")
        elif service_manager.systemd_available and choice == '4':
            manage_systemd_install_menu()
        elif not (service_manager.systemd_available and choice in ['3', '4']) and choice not in ['1', '2', '0']:
             print_fast(f"{COLOR_ERROR}❌ Invalid choice.{RESET_COLOR}")
             input("\nPress Enter to continue...")


def manage_allowed_users_menu():
    """
    Displays and handles the menu for managing allowed user IDs.
    """
    while True:
        clear_screen()
        config = config_manager.get_config()
        bot_config = config.get("bot", {})
        allowed_ids = bot_config.get("allowed_user_ids", [])

        print_fast(f"{COLOR_TITLE}\n--- Manage Allowed User IDs ---{RESET_COLOR}")
        if allowed_ids:
            print_fast(f"Current IDs: {', '.join(map(str, allowed_ids))}")
        else:
            print_fast(f"{COLOR_WARNING}Current IDs: None (This means all users are allowed to interact with the bot){RESET_COLOR}")

        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        print_fast("1. Add User ID")
        print_fast("2. Remove User ID")
        print_fast("3. Import IDs from CSV file")
        print_fast("4. Clear all User IDs")
        print_fast("0. Back to Telegram Bot Settings")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")
        
        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            new_id = get_numeric_input("Enter the user ID to add: ", int)
            if new_id:
                if new_id not in allowed_ids:
                    allowed_ids.append(new_id)
                    config_manager.save_config()
                    print_fast(f"{COLOR_SUCCESS}✅ User ID {new_id} added.{RESET_COLOR}")
                    logger.info(f"Added Telegram bot allowed user ID: {new_id}")
                else:
                    print_fast(f"{COLOR_WARNING}⚠️ User ID {new_id} is already in the list.{RESET_COLOR}")
            input("\nPress Enter to continue...")

        elif choice == "2":
            id_to_remove = get_numeric_input("Enter the user ID to remove: ", int)
            if id_to_remove:
                if id_to_remove in allowed_ids:
                    allowed_ids.remove(id_to_remove)
                    config_manager.save_config()
                    print_fast(f"{COLOR_SUCCESS}✅ User ID {id_to_remove} removed.{RESET_COLOR}")
                    logger.info(f"Removed Telegram bot allowed user ID: {id_to_remove}")
                else:
                    print_fast(f"{COLOR_ERROR}❌ User ID {id_to_remove} not found in the list.{RESET_COLOR}")
            input("\nPress Enter to continue...")

        elif choice == "3":
            file_path = get_user_input("Enter the full path to the CSV file: ")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv.reader(f)
                        imported_ids = []
                        for row in reader:
                            for item in row:
                                try:
                                    imported_ids.append(int(item.strip()))
                                except ValueError:
                                    pass # Ignore non-integer values
                        
                        newly_added_ids = sorted(list(set(uid for uid in imported_ids if uid not in allowed_ids)))
                        if newly_added_ids:
                            allowed_ids.extend(newly_added_ids)
                            config_manager.save_config()
                            print_fast(f"{COLOR_SUCCESS}✅ Imported {len(newly_added_ids)} new user IDs.{RESET_COLOR}")
                            logger.info(f"Imported {len(newly_added_ids)} new Telegram bot allowed user IDs from {file_path}")
                        else:
                            print_fast(f"{COLOR_INFO}ℹ️ No new user IDs to import.{RESET_COLOR}")
                            
                        duplicates = len(imported_ids) - len(newly_added_ids)
                        if duplicates > 0:
                            print_fast(f"{COLOR_INFO}ℹ️ {duplicates} IDs were duplicates or invalid and were ignored.{RESET_COLOR}")

                except Exception as e:
                    logger.error(f"Error importing Telegram bot user IDs from CSV: {e}")
                    print_fast(f"{COLOR_ERROR}❌ Error reading file: {e}{RESET_COLOR}")
            else:
                print_fast(f"{COLOR_ERROR}❌ File not found at '{file_path}'.{RESET_COLOR}")
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            if confirm_action("Are you sure you want to remove all allowed user IDs?"):
                if allowed_ids:
                    allowed_ids.clear()
                    config_manager.save_config()
                    print_fast(f"{COLOR_SUCCESS}✅ All user IDs have been cleared.{RESET_COLOR}")
                    logger.info("Cleared all Telegram bot allowed user IDs.")
                else:
                    print_fast(f"{COLOR_INFO}ℹ️ The list is already empty.{RESET_COLOR}")
            else:
                print_fast(f"{COLOR_INFO}Action cancelled.{RESET_COLOR}")
            input("\nPress Enter to continue...")

        elif choice == "0":
            break
        else:
            print_fast(f"{COLOR_ERROR}❌ Invalid choice.{RESET_COLOR}")
            input("\nPress Enter to continue...")


def telegram_bot_menu():
    """
    Displays and handles the Telegram bot settings menu.
    """
    while True:
        clear_screen()
        config = config_manager.get_config()
        bot_config = config.get("bot", {})
        
        enabled_status = f"{COLOR_SUCCESS}Enabled{RESET_COLOR}" if bot_config.get("enabled") else f"{COLOR_WARNING}Disabled{RESET_COLOR}"
        token_status = f"{COLOR_SUCCESS}Set{RESET_COLOR}" if bot_config.get("token") else f"{COLOR_WARNING}Not Set{RESET_COLOR}"
        user_ids_count = len(bot_config.get("allowed_user_ids", []))
        service_status = service_manager.get_status()

        print_fast(f"{COLOR_TITLE}\n--- Telegram Bot Settings ---{RESET_COLOR}")
        print_fast(f"Status: {enabled_status} | Token: {token_status} | Allowed Users: {user_ids_count} | Service: {service_status}")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")
        
        print_fast(f"1. {'Disable' if bot_config.get('enabled') else 'Enable'} Bot")
        print_fast("2. Set/Update Token")
        print_fast("3. Manage Allowed User IDs")
        print_fast("4. Manage Service")
        print_fast("0. Back to Settings Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            current_status = bot_config.get("enabled", False)
            if not current_status and not bot_config.get("token"):
                print_fast(f"{COLOR_WARNING}⚠️ Cannot enable bot: Token is not set.{RESET_COLOR}")
                print_fast("Please set a token first.")
                input("\nPress Enter to continue...")
                continue
            
            bot_config["enabled"] = not current_status
            config_manager.save_config()
            
            new_status_text = "Enabled" if not current_status else "Disabled"
            print_fast(f"{COLOR_SUCCESS}✅ Bot has been {new_status_text}.{RESET_COLOR}")
            logger.info(f"Telegram bot has been {new_status_text}.")
            input("Press Enter to continue...")

        elif choice == "2":
            current_token = bot_config.get('token', '')
            current_token_display = f" (current: ...{current_token[-4:]})" if current_token else ""
            prompt = f"Enter new Telegram Bot Token{current_token_display} or press Enter to cancel: "
            new_token = _get_sanitized_input(prompt)

            if new_token:
                if ':' not in new_token or not new_token.split(':')[0].isdigit():
                     print_fast(f"{COLOR_ERROR}❌ Invalid token format. It should look like '123456:ABC-DEF1234...'.{RESET_COLOR}")
                     input("\nPress Enter to continue...")
                     continue

                bot_config["token"] = new_token
                config_manager.save_config()
                print_fast(f"{COLOR_SUCCESS}✅ Bot token has been updated.{RESET_COLOR}")
                logger.info("Telegram bot token has been updated.")
                print_fast(f"{COLOR_INFO}ℹ️ If the bot service is running, please restart it for the new token to take effect.{RESET_COLOR}")
            else:
                print_fast(f"{COLOR_INFO}No token entered. The token was not changed.{RESET_COLOR}")
            input("\nPress Enter to continue...")

        elif choice == "3":
            manage_allowed_users_menu()

        elif choice == "4":
            manage_service_menu()
            
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice in Telegram Bot menu: {choice}")
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
            input("Press Enter to continue...")
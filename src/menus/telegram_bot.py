"""
Telegram Bot Settings Menu.

This module provides the user interface for managing the Telegram bot settings,
guiding the user through either an initial setup or a management menu.
"""
import csv
import os
import subprocess
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .utils import clear_screen, get_user_input, get_numeric_input, confirm_action, _get_sanitized_input
from ..core.config import config_manager
from ..core.service_manager import service_manager
from ..display import *
from ..core.logger import logger, LOGS_DIR
from ..bot.i18n import t

def _send_telegram_message(token, chat_id, text, reply_markup=None):
    """Sends a message to a given chat ID using the bot's token."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup.to_json()
        
    try:
        response = requests.post(url, json=payload, timeout=5)
        if not response.json().get("ok"):
            logger.warning(f"Failed to send message to {chat_id}: {response.text}")
            return False
        return True
    except requests.RequestException as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

def _notify_users_on_start(bot_settings, message_key):
    """Notifies all allowed users when the bot starts or restarts."""
    token = bot_settings.get("token")
    user_ids = bot_settings.get("allowed_user_ids", [])
    lang = bot_settings.get("lang", {}).get("default", "en")
    if not token or not user_ids:
        return

    keyboard = [[InlineKeyboardButton(t("start_button", lang), callback_data="menu_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = t(message_key, lang)

    for user_id in user_ids:
        _send_telegram_message(token, user_id, message, reply_markup=reply_markup)

def _validate_telegram_token(token):
    """Validates a Telegram bot token by calling the getMe endpoint."""
    if not token or ':' not in token or not token.split(':')[0].isdigit():
        return False, "Invalid token format."
    
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and response.json().get("ok"):
            bot_name = response.json().get("result", {}).get("username")
            return True, bot_name
        else:
            error_description = response.json().get("description", "Unknown error from Telegram API")
            return False, f"Telegram API error: {error_description}"
    except requests.RequestException as e:
        return False, f"Connection error: {e}"

def _setup_bot_interactive():
    """Guides the user through the initial interactive setup of the bot."""
    clear_screen()
    print_fast(f"{COLOR_TITLE}\n--- Telegram Bot Setup ---{RESET_COLOR}")
    
    # Step 1: Get API Token
    print_fast(f"\n{COLOR_INFO}To begin, you need a Telegram Bot Token from @BotFather on Telegram.{RESET_COLOR}")
    print_fast(f"{COLOR_INFO}Instructions can be found at: https://t.me/BotFather{RESET_COLOR}")
    
    token = ""
    while True:
        prompt = "Please enter your Telegram Bot Token (or press Enter to cancel): "
        token = _get_sanitized_input(prompt)
        if not token:
            print_fast(f"{COLOR_INFO}Setup cancelled.{RESET_COLOR}")
            input("\nPress Enter to continue...")
            return
        
        print_fast(f"{COLOR_INFO}Validating token...{RESET_COLOR}")
        is_valid, message = _validate_telegram_token(token)
        
        if is_valid:
            print_fast(f"{COLOR_SUCCESS}✅ Token validated successfully for bot: @{message}{RESET_COLOR}")
            break
        else:
            print_fast(f"{COLOR_ERROR}❌ Token validation failed: {message}{RESET_COLOR}")
            if not confirm_action("Try again?"):
                return
    
    # Step 2: Get Allowed User IDs
    print_fast(f"\n{COLOR_INFO}Next, enter the allowed Telegram User IDs, separated by commas.{RESET_COLOR}")
    print_fast(f"{COLOR_INFO}Only these users can interact with your bot. Find a user's ID via bots like @userinfobot.{RESET_COLOR}")
    print_fast(f"{COLOR_INFO}If needed, you can also use @ShowChatIdBot at https://t.me/ShowChatIdBot.{RESET_COLOR}")
    
    user_ids = []
    while True:
        ids_str = get_user_input("Enter allowed User IDs (e.g., 12345, 67890): ")
        try:
            user_ids = [int(uid.strip()) for uid in ids_str.split(',') if uid.strip()]
            if user_ids:
                break
            else:
                print_fast(f"{COLOR_ERROR}❌ Please enter at least one valid numeric User ID.{RESET_COLOR}")
        except ValueError:
            print_fast(f"{COLOR_ERROR}❌ Invalid input. Please enter only numeric IDs separated by commas.{RESET_COLOR}")

    # Step 3: Save configuration
    config = config_manager.get_config()
    bot_settings = config.setdefault("settings", {}).setdefault("bot", {})
    bot_settings["token"] = token
    bot_settings["allowed_user_ids"] = user_ids
    bot_settings["enabled"] = True
    config_manager.save_config()
    
    print_fast(f"\n{COLOR_SUCCESS}✅ Configuration saved successfully.{RESET_COLOR}")
    logger.info("Telegram bot configured with new token and user IDs.")

    # Step 4: Install and start service
    print_fast(f"\n{COLOR_INFO}Installing and starting the bot service...{RESET_COLOR}")
    
    if service_manager.systemd_available:
        install_success, message = service_manager.install_service()
        if install_success:
            print_fast(f"{COLOR_SUCCESS}✅ {message}{RESET_COLOR}")
        else:
            print_fast(f"{COLOR_ERROR}❌ {message}{RESET_COLOR}")
            input("\nPress Enter to continue...")
            return

    start_success, message = service_manager.start_service()
    if start_success:
        print_fast(f"{COLOR_SUCCESS}✅ Bot service started successfully.{RESET_COLOR}")
        _notify_users_on_start(bot_settings, "bot_setup_and_started")
    else:
        print_fast(f"{COLOR_ERROR}❌ {message}{RESET_COLOR}")

    print_fast(f"\n{COLOR_SUCCESS}Bot successfully set up and service installed!{RESET_COLOR}")
    input("\nPress Enter to return to the menu...")

def _delete_bot():
    """Deletes the bot's configuration and uninstalls the service."""
    clear_screen()
    print_fast(f"{COLOR_TITLE}\n--- Delete Bot ---{RESET_COLOR}")
    print_fast(f"{COLOR_WARNING}This will stop the bot, uninstall the service, and remove all bot configurations.{RESET_COLOR}")
    
    if not confirm_action("Are you sure you want to delete the bot?"):
        print_fast(f"{COLOR_INFO}Deletion cancelled.{RESET_COLOR}")
        input("\nPress Enter to continue...")
        return

    service_manager.stop_service()
    if service_manager.systemd_available:
        service_manager.uninstall_service()

    config = config_manager.get_config()
    bot_settings = config.setdefault("settings", {}).setdefault("bot", {})
    bot_settings["enabled"] = False
    bot_settings["token"] = ""
    bot_settings["allowed_user_ids"] = []
    config_manager.save_config()

    print_fast(f"\n{COLOR_SUCCESS}✅ Bot has been successfully deleted.{RESET_COLOR}")
    logger.info("Telegram bot has been deleted.")
    input("\nPress Enter to return to the main menu...")

def _view_logs():
    """Displays the live logs for the bot."""
    clear_screen()
    log_file = os.path.join(LOGS_DIR, "app.log")
    print_fast(f"{COLOR_TITLE}\n--- Viewing Bot Logs ---{RESET_COLOR}")
    print_fast(f"Displaying logs from: {log_file}")
    print_fast("Press Ctrl+C to stop viewing.")
    
    try:
        if not os.path.exists(log_file):
            print_fast(f"{COLOR_WARNING}Log file not found.{RESET_COLOR}")
            input("\nPress Enter to continue...")
            return
            
        subprocess.run(["tail", "-f", log_file], check=True)
    except (KeyboardInterrupt, subprocess.CalledProcessError):
        pass
    finally:
        print_fast("\nStopped viewing logs.")
        input("\nPress Enter to return to the menu...")

def manage_allowed_users_menu():
    """Manages the list of allowed user IDs."""
    while True:
        clear_screen()
        config = config_manager.get_config()
        bot_settings = config.get("settings", {}).get("bot", {})
        allowed_ids = bot_settings.get("allowed_user_ids", [])

        print_fast(f"{COLOR_TITLE}\n--- Manage Allowed User IDs ---{RESET_COLOR}")
        if allowed_ids:
            print_fast(f"Current IDs: {', '.join(map(str, allowed_ids))}")
        else:
            print_fast(f"{COLOR_WARNING}Current IDs: None (All users can interact with the bot){RESET_COLOR}")

        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")
        print_fast("1. Add User ID")
        print_fast("2. Remove User ID")
        print_fast("3. Import IDs from CSV file")
        print_fast("4. Clear all User IDs")
        print_fast("0. Back")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")
        
        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            new_id = get_numeric_input("Enter the user ID to add: ", int)
            if new_id and new_id not in allowed_ids:
                allowed_ids.append(new_id)
                config_manager.save_config()
                print_fast(f"{COLOR_SUCCESS}✅ User ID {new_id} added.{RESET_COLOR}")
            elif new_id:
                print_fast(f"{COLOR_WARNING}⚠️ User ID {new_id} is already in the list.{RESET_COLOR}")
            input("\nPress Enter to continue...")

        elif choice == "2":
            id_to_remove = get_numeric_input("Enter the user ID to remove: ", int)
            if id_to_remove and id_to_remove in allowed_ids:
                allowed_ids.remove(id_to_remove)
                config_manager.save_config()
                print_fast(f"{COLOR_SUCCESS}✅ User ID {id_to_remove} removed.{RESET_COLOR}")
            elif id_to_remove:
                print_fast(f"{COLOR_ERROR}❌ User ID {id_to_remove} not found.{RESET_COLOR}")
            input("\nPress Enter to continue...")

        elif choice == "3":
            file_path = get_user_input("Enter the full path to the CSV file: ")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv.reader(f)
                        imported_ids = {int(item.strip()) for row in reader for item in row if item.strip().isdigit()}
                        newly_added_ids = sorted([uid for uid in imported_ids if uid not in allowed_ids])
                        if newly_added_ids:
                            allowed_ids.extend(newly_added_ids)
                            config_manager.save_config()
                            print_fast(f"{COLOR_SUCCESS}✅ Imported {len(newly_added_ids)} new user IDs.{RESET_COLOR}")
                        else:
                            print_fast(f"{COLOR_INFO}ℹ️ No new user IDs to import.{RESET_COLOR}")
                except Exception as e:
                    print_fast(f"{COLOR_ERROR}❌ Error reading file: {e}{RESET_COLOR}")
            else:
                print_fast(f"{COLOR_ERROR}❌ File not found.{RESET_COLOR}")
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            if confirm_action("Are you sure you want to remove all allowed user IDs?"):
                if allowed_ids:
                    allowed_ids.clear()
                    config_manager.save_config()
                    print_fast(f"{COLOR_SUCCESS}✅ All user IDs have been cleared.{RESET_COLOR}")
            input("\nPress Enter to continue...")

        elif choice == "0":
            break
        else:
            print_fast(f"{COLOR_ERROR}❌ Invalid choice.{RESET_COLOR}")
            input("\nPress Enter to continue...")

def telegram_bot_menu(from_settings=False):
    """
    Displays and handles the Telegram bot settings menu.
    
    Args:
        from_settings (bool): If True, the "Back" button will return to the
                              main settings menu. Otherwise, it exits.
    """
    while True:
        clear_screen()
        config = config_manager.get_config()
        bot_settings = config.get("settings", {}).get("bot", {})
        is_setup = bot_settings.get("token")

        back_text = "Back to Settings Menu" if from_settings else "Back to Main Menu"

        if not is_setup:
            print_fast(f"{COLOR_TITLE}\n--- Telegram Bot Settings ---{RESET_COLOR}")
            print_fast(f"{COLOR_WARNING}The bot is not set up yet. Would you like to set it up now?{RESET_COLOR}")
            print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")
            print_fast("1. Yes, set up the bot")
            print_fast(f"0. No, {back_text.lower()}")
            print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")
            
            choice = input("👉 Enter your choice: ").strip()
            if choice == '1':
                _setup_bot_interactive()
            elif choice == '0':
                break
            else:
                print_fast(f"{COLOR_ERROR}❌ Invalid choice.{RESET_COLOR}")
                input("\nPress Enter to continue...")
        else:
            enabled_status = f"{COLOR_SUCCESS}Enabled{RESET_COLOR}" if bot_settings.get("enabled") else f"{COLOR_WARNING}Disabled{RESET_COLOR}"
            token_status = f"{COLOR_SUCCESS}Set{RESET_COLOR}"
            user_ids_count = len(bot_settings.get("allowed_user_ids", []))
            service_status = service_manager.get_status()

            print_fast(f"{COLOR_TITLE}\n--- Telegram Bot Management ---{RESET_COLOR}")
            print_fast(f"Status: {enabled_status} | Token: {token_status} | Users: {user_ids_count} | Service: {service_status}")
            print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")
            
            print_fast(f"1. {'Disable' if bot_settings.get('enabled') else 'Enable'} Bot")
            print_fast("2. Edit Token")
            print_fast("3. Manage Allowed User IDs")
            print_fast("4. Restart Bot")
            print_fast("5. View Logs")
            print_fast("6. Delete Bot")
            print_fast(f"0. {back_text}")
            print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

            choice = input("👉 Enter your choice: ").strip()

            if choice == "1": # Enable/Disable Bot
                new_status = not bot_settings.get("enabled", False)
                bot_settings["enabled"] = new_status
                config_manager.save_config()
                
                status_text = "Enabled" if new_status else "Disabled"
                action_text = "started" if new_status else "stopped"
                
                if new_status:
                    success, message = service_manager.start_service()
                    if success:
                        _notify_users_on_start(bot_settings, "bot_enabled_and_started")
                else:
                    success, message = service_manager.stop_service()
                
                if success:
                    print_fast(f"{COLOR_SUCCESS}✅ Bot has been {status_text} and the service was {action_text}.{RESET_COLOR}")
                else:
                    print_fast(f"{COLOR_ERROR}❌ Failed to {action_text} the service: {message}{RESET_COLOR}")
                input("\nPress Enter to continue...")

            elif choice == "2": # Edit Token
                current_token = bot_settings.get('token', '')
                current_token_display = f" (current: ...{current_token[-4:]})"
                prompt = f"Enter new Telegram Bot Token{current_token_display} or press Enter to cancel: "
                new_token = _get_sanitized_input(prompt)

                if new_token:
                    print_fast(f"{COLOR_INFO}Validating new token...{RESET_COLOR}")
                    is_valid, message = _validate_telegram_token(new_token)
                    
                    if is_valid:
                        print_fast(f"{COLOR_SUCCESS}✅ Token validated for bot: @{message}{RESET_COLOR}")
                        bot_settings["token"] = new_token
                        config_manager.save_config()
                        print_fast(f"{COLOR_SUCCESS}✅ Bot token updated. Restarting service...{RESET_COLOR}")
                        success, restart_message = service_manager.restart_service()
                        if success:
                            print_fast(f"{COLOR_SUCCESS}✅ Service restarted successfully.{RESET_COLOR}")
                            _notify_users_on_start(bot_settings, "bot_restarted_new_token")
                        else:
                            print_fast(f"{COLOR_ERROR}❌ {restart_message}{RESET_COLOR}")
                    else:
                        print_fast(f"{COLOR_ERROR}❌ New token is invalid: {message}{RESET_COLOR}")
                else:
                    print_fast(f"{COLOR_INFO}Token update cancelled.{RESET_COLOR}")
                input("\nPress Enter to continue...")

            elif choice == "3":
                manage_allowed_users_menu()

            elif choice == "4":
                print_fast(f"{COLOR_INFO}Restarting bot service...{RESET_COLOR}")
                success, message = service_manager.restart_service()
                if success:
                    print_fast(f"{COLOR_SUCCESS}✅ Service restarted successfully.{RESET_COLOR}")
                    _notify_users_on_start(bot_settings, "bot_restarted")
                else:
                    print_fast(f"{COLOR_ERROR}❌ {message}{RESET_COLOR}")
                input("\nPress Enter to continue...")

            elif choice == "5":
                _view_logs()

            elif choice == "6":
                _delete_bot()

            elif choice == "0":
                break
            else:
                print_fast(f"{COLOR_ERROR}❌ Invalid choice.{RESET_COLOR}")
                input("\nPress Enter to continue...")
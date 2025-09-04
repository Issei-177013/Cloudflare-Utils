"""
Application Settings Menu.

This module provides the user interface for managing global application settings,
such as toggling console logging.
"""
import importlib
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones
from .utils import clear_screen
from ..core.config import config_manager
from ..core.logger import logger, configure_console_logging
from ..display import *
from .. import display
from .utils import get_numeric_input, get_validated_input
from .telegram_bot import telegram_bot_menu

def general_settings_menu():
    """
    Displays and handles the general settings menu.
    """
    while True:
        clear_screen()
        config = config_manager.get_config()
        current_timezone = config.get("settings", {}).get("global", {}).get("timezone", "UTC")

        print_fast(f"{COLOR_TITLE}\n--- General Settings ---{RESET_COLOR}")
        print_fast(f"1. Configure Time Zone: {current_timezone}")
        print_fast("0. Back to Settings Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            def is_valid_timezone(tz_name):
                return tz_name in available_timezones()

            prompt_text = "Enter your preferred time zone (e.g., UTC, Europe/Berlin, Asia/Tehran): "
            error_text = "Invalid IANA time zone. Please try again."
            
            new_timezone = get_validated_input(prompt_text, is_valid_timezone, error_text)

            if new_timezone:
                config.setdefault("settings", {}).setdefault("global", {})["timezone"] = new_timezone
                config_manager.save_config()
                print_fast(f"{COLOR_SUCCESS}✅ Time zone updated to {new_timezone}.{RESET_COLOR}")
                logger.info(f"Time zone setting changed to: {new_timezone}")
            else:
                print_fast(f"{COLOR_WARNING}Time zone configuration cancelled.{RESET_COLOR}")
            input("Press Enter to continue...")

        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice in general settings menu: {choice}")
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
            input("Press Enter to continue...")

def cli_settings_menu():
    """
    Displays and handles the CLI settings menu.
    """
    while True:
        clear_screen()
        config = config_manager.get_config()
        
        cli_settings = config.get("settings", {}).get("cli", {})
        console_logging_status = "Enabled" if cli_settings.get("console_logging", False) else "Disabled"
        slow_mode_status = "Enabled" if not get_fast_mode_status() else "Disabled"
        current_delay = get_slow_mode_delay()

        print_fast(f"{COLOR_TITLE}\n--- CLI Settings ---{RESET_COLOR}")
        print_fast(f"1. Console Logging: {console_logging_status}")
        print_fast(f"2. Slow Mode: {slow_mode_status}")
        print_fast(f"3. Slow Mode Delay: {current_delay}s")
        print_fast("0. Back to Settings Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            cli_settings["console_logging"] = not cli_settings.get("console_logging", False)
            config_manager.save_config()
            configure_console_logging(config)
            new_status_str = "Enabled" if cli_settings["console_logging"] else "Disabled"
            print_fast(f"{COLOR_SUCCESS}✅ Console logging has been {new_status_str}.{RESET_COLOR}")
            logger.info(f"Console logging setting changed to: {cli_settings['console_logging']}")
            input("Press Enter to continue...")

        elif choice == "2":
            cli_settings["fast_mode"] = not cli_settings.get("fast_mode", True)
            config_manager.save_config()
            importlib.reload(display)
            new_status = "Enabled" if not cli_settings["fast_mode"] else "Disabled"
            print_fast(f"{COLOR_SUCCESS}✅ Slow Mode has been {new_status}.{RESET_COLOR}")
            logger.info(f"Slow Mode (fast_mode) setting changed to: {not cli_settings['fast_mode']}")
            input("Press Enter to continue...")
            
        elif choice == "3":
            new_delay = get_numeric_input(
                f"Enter new delay in seconds (e.g., 0.01). Current is {current_delay}: ",
                float, min_val=0.0, max_val=1.0
            )
            if new_delay is not None:
                cli_settings["slow_mode_delay"] = new_delay
                config_manager.save_config()
                importlib.reload(display)
                print_fast(f"{COLOR_SUCCESS}✅ Slow mode delay updated to {new_delay}s.{RESET_COLOR}")
                logger.info(f"Slow mode delay changed to: {new_delay}")
            else:
                print_fast(f"{COLOR_ERROR}Invalid input. Delay not changed.{RESET_COLOR}")
            input("Press Enter to continue...")

        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice in CLI settings menu: {choice}")
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
            input("Press Enter to continue...")

def settings_menu():
    """
    Displays and handles the application settings menu.
    """
    while True:
        clear_screen()
        print_fast(f"{COLOR_TITLE}\n--- Settings ---{RESET_COLOR}")
        print_fast("1. General Settings")
        print_fast("2. CLI Settings")
        print_fast("3. Telegram Bot Settings")
        print_fast("0. Back to Main Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            general_settings_menu()
        elif choice == "2":
            cli_settings_menu()
        elif choice == "3":
            telegram_bot_menu(from_settings=True)
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice in settings menu: {choice}")
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
            input("Press Enter to continue...")
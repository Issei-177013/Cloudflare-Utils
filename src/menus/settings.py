"""
Application Settings Menu.

This module provides the user interface for managing global application settings,
such as toggling console logging.
"""
import importlib
from .utils import clear_screen
from ..config import load_config, save_config
from ..logger import logger, setup_logger
from ..display import print_slow, OPTION_SEPARATOR, get_fast_mode_status
from .. import display

def settings_menu():
    """
    Displays and handles the application settings menu.

    This function allows the user to view and modify application-wide
    settings. Currently, it supports toggling console logging on or off.
    """
    while True:
        clear_screen()
        config = load_config()
        console_logging_status = "Enabled" if config.get("settings", {}).get("console_logging", True) else "Disabled"
        fast_mode_status = "Enabled" if get_fast_mode_status() else "Disabled"

        print_slow("\n--- Settings ---")
        print_slow(f"1. Console Logging: {console_logging_status}")
        print_slow(f"2. Fast Mode (slow text effect): {fast_mode_status}")
        print_slow("0. Back to Main Menu")
        print_slow(OPTION_SEPARATOR)

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            current_status = config.get("settings", {}).get("console_logging", True)
            if "settings" not in config:
                config["settings"] = {}
            config["settings"]["console_logging"] = not current_status
            save_config(config)
            
            # Reconfigure the logger to apply the change immediately.
            setup_logger()

            new_status = "Enabled" if not current_status else "Disabled"
            print_slow(f"✅ Console logging has been {new_status}.")
            logger.info(f"Console logging setting changed to: {not current_status}")
            input("Press Enter to continue...")
        elif choice == "2":
            current_status = get_fast_mode_status()
            if "settings" not in config:
                config["settings"] = {}
            config["settings"]["fast_mode"] = not current_status
            save_config(config)

            # Reload the display module to update the FAST_MODE global variable
            importlib.reload(display)
            
            new_status = "Enabled" if not current_status else "Disabled"
            print_slow(f"✅ Fast Mode has been {new_status}.")
            logger.info(f"Fast Mode setting changed to: {not current_status}")
            input("Press Enter to continue...")
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice in settings menu: {choice}")
            print_slow("❌ Invalid choice. Please select a valid option.")
            input("Press Enter to continue...")
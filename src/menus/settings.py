"""
Application Settings Menu.

This module provides the user interface for managing global application settings,
such as toggling console logging.
"""
import importlib
from .utils import clear_screen
from ..core.config import config_manager
from ..core.logger import logger, configure_console_logging
from ..display import *
from .. import display
from .utils import get_numeric_input
from .telegram_bot import telegram_bot_menu

def settings_menu():
    """
    Displays and handles the application settings menu.
    """
    while True:
        clear_screen()
        config = config_manager.get_config()
        
        # Get current settings
        console_logging_status = "Enabled" if config.get("settings", {}).get("console_logging", False) else "Disabled"
        slow_mode_status = "Enabled" if not get_fast_mode_status() else "Disabled"
        current_delay = get_slow_mode_delay()

        print_fast(f"{COLOR_TITLE}\n--- Settings ---{RESET_COLOR}")
        print_fast(f"1. Console Logging: {console_logging_status}")
        print_fast(f"2. Slow Mode: {slow_mode_status}")
        print_fast(f"3. Slow Mode Delay: {current_delay}s")
        print_fast("4. Telegram Bot")
        print_fast("0. Back to Main Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            # Toggle the console_logging setting
            settings = config.setdefault("settings", {})
            current_status = settings.get("console_logging", False)
            new_status_bool = not current_status
            settings["console_logging"] = new_status_bool
            
            # Save the configuration
            config_manager.save_config()
            
            # Immediately apply the new logging configuration
            configure_console_logging(config)
            
            # Notify the user
            new_status_str = "Enabled" if new_status_bool else "Disabled"
            print_fast(f"{COLOR_SUCCESS}✅ Console logging has been {new_status_str}.{RESET_COLOR}")
            logger.info(f"Console logging setting changed to: {new_status_bool}")
            input("Press Enter to continue...")

        elif choice == "2":
            current_status = get_fast_mode_status()
            if "settings" not in config: config["settings"] = {}
            config["settings"]["fast_mode"] = not current_status
            config_manager.save_config()
            importlib.reload(display) # Reload to update FAST_MODE global
            new_status = "Enabled" if current_status else "Disabled"
            print_fast(f"{COLOR_SUCCESS}✅ Slow Mode has been {new_status}.{RESET_COLOR}")
            logger.info(f"Slow Mode (fast_mode) setting changed to: {not current_status}")
            input("Press Enter to continue...")
            
        elif choice == "3":
            new_delay = get_numeric_input(
                f"Enter new delay in seconds (e.g., 0.01). Current is {current_delay}: ",
                float,
                min_val=0.0,
                max_val=1.0
            )
            if new_delay is not None:
                if "settings" not in config: config["settings"] = {}
                config["settings"]["slow_mode_delay"] = new_delay
                config_manager.save_config()
                importlib.reload(display) # Reload to update delay
                print_fast(f"{COLOR_SUCCESS}✅ Slow mode delay updated to {new_delay}s.{RESET_COLOR}")
                logger.info(f"Slow mode delay changed to: {new_delay}")
            else:
                print_fast(f"{COLOR_ERROR}Invalid input. Delay not changed.{RESET_COLOR}")
            input("Press Enter to continue...")

        elif choice == "4":
            telegram_bot_menu()

        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice in settings menu: {choice}")
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
            input("Press Enter to continue...")
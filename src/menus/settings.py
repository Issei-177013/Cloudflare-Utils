from .utils import clear_screen
from ..config import load_config, save_config
from ..logger import logger, setup_logger

def settings_menu():
    """
    Menu for managing application settings.
    """
    while True:
        clear_screen()
        config = load_config()
        console_logging_status = "Enabled" if config.get("settings", {}).get("console_logging", True) else "Disabled"

        print("\n--- Settings ---")
        print(f"1. Console Logging: {console_logging_status}")
        print("0. Back to Main Menu")
        print("-----------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            # Toggle console logging
            current_status = config.get("settings", {}).get("console_logging", True)
            config["settings"]["console_logging"] = not current_status
            save_config(config)
            
            # Reconfigure logger to apply changes immediately
            setup_logger()

            new_status = "Enabled" if not current_status else "Disabled"
            print(f"✅ Console logging has been {new_status}.")
            logger.info(f"Console logging setting changed to: {not current_status}")
            input("Press Enter to continue...")
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice in settings menu: {choice}")
            print("❌ Invalid choice. Please select a valid option.")
            input("Press Enter to continue...")
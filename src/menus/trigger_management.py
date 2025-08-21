"""
Menu for Trigger Management.
"""
from ..config import load_config, save_config
from ..display import print_fast, print_slow, COLOR_TITLE, COLOR_SEPARATOR, OPTION_SEPARATOR, RESET_COLOR, COLOR_ERROR
from ..input_helper import get_user_input
from ..logger import logger
from ..triggers import add_trigger, edit_trigger, delete_trigger, list_triggers
from .utils import clear_screen

def trigger_management_menu():
    """Main menu for managing triggers."""
    while True:
        clear_screen()
        print_fast(f"{COLOR_TITLE}--- Trigger Management ---{RESET_COLOR}")
        
        list_triggers()
        
        print_fast("\n1. Add New Trigger")
        print_fast("2. Edit a Trigger")
        print_fast("3. Delete a Trigger")
        print_fast("0. Back to Traffic Monitoring Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = get_user_input("Enter your choice: ")

        if choice == '1':
            config = load_config()
            add_trigger(config)
            save_config(config) # add_trigger stages changes, we save them here.
            input("\nPress Enter to continue...")
        elif choice == '2':
            edit_trigger()
            input("\nPress Enter to continue...")
        elif choice == '3':
            delete_trigger()
            input("\nPress Enter to continue...")
        elif choice == '0':
            break
        else:
            logger.warning(f"Invalid choice in trigger menu: {choice}")
            print_fast(f"{COLOR_ERROR}Invalid choice.{RESET_COLOR}")
            input("\nPress Enter to continue...")
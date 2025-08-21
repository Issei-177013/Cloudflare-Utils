"""
IP Rotator Tools Main Menu.

This module serves as the entry point for all IP rotation-related tools.
It provides a navigation menu to access different rotation strategies,
such as single-record rotation, multi-record rotation, and swapping IPs
between existing records.
"""
from ..logger import logger
from .utils import clear_screen
from .rotator_single_record import rotate_based_on_list_of_ips_single_record_menu
from .rotator_multi_record import rotate_based_on_list_of_ips_multi_record_menu
from .rotator_record_group import rotate_ips_between_records_management_menu
from ..display import (
    display_as_table, display_token_guidance, print_slow, print_fast,
    HEADER_LINE, OPTION_SEPARATOR, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_INFO, RESET_COLOR, COLOR_TITLE, COLOR_SEPARATOR
)

def rotator_tools_menu():
    """
    Displays and handles the main menu for IP Rotator Tools.
    """
    clear_screen()
    while True:
        print_fast(f"\n{COLOR_TITLE}--- IP Rotator Tools ---{RESET_COLOR}")
        print_slow("1. 🔄 Rotate Based on a List of IPs (Single-Record)")
        print_slow("2. 🌍 Rotate Based on a List of IPs (Multi-Records)")
        print_slow("3. 🔀 Rotate IPs Between Records")
        print_slow("0. ⬅️ Return to Main Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = input("👉 Enter your choice: ").strip()

        if choice == "1":
            rotate_based_on_list_of_ips_single_record_menu()
        elif choice == "2":
            rotate_based_on_list_of_ips_multi_record_menu()
        elif choice == "3":
            rotate_ips_between_records_management_menu()
        elif choice == "0":
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
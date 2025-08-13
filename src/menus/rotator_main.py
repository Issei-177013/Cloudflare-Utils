from ..logger import logger
from .utils import clear_screen
from .rotator_single_record import rotate_based_on_list_of_ips_single_record_menu
from .rotator_multi_record import rotate_based_on_list_of_ips_multi_record_menu
from .rotator_record_group import rotate_ips_between_records_management_menu

def rotator_tools_menu():
    """Displays the Rotator Tools submenu."""
    clear_screen()
    while True:
        print("\n--- IP Rotator Tools ---")
        print("1. 🔄 Rotate Based on a List of IPs (Single-Record)")
        print("2. 🌍 Rotate Based on a List of IPs (Multi-Records)")
        print("3. 🔀 Rotate IPs Between Records")
        print("0. ⬅️ Return to Main Menu")
        print("---------------------")

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
            print("❌ Invalid choice. Please select a valid option.")
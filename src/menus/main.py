"""
Main Menu for the Cloudflare Utils CLI.

This module displays the main navigation menu for the command-line interface.
It allows the user to access different functionalities of the application,
such as account management, zone management, DNS tools, and settings.
"""
try:
    from version import __version__
    version_str = f"Version: {__version__}"
except ImportError:
    version_str = "Version: N/A"

from ..logger import logger
from .utils import clear_screen, confirm_action, view_live_logs
from .accounts import account_management_menu
from .zones import zone_management_menu
from .dns import dns_management_menu
from .rotator_main import rotator_tools_menu
from .settings import settings_menu
from .traffic_monitoring import traffic_monitoring_menu
from ..display import print_slow, HEADER_LINE, FOOTER_LINE, OPTION_SEPARATOR

def main_menu():
    """
    Displays and handles the main menu of the application.

    This function runs in a loop, presenting the user with a list of
    options to navigate to different parts of the application. It handles
    user input and calls the appropriate menu function based on the user's
    choice. The loop continues until the user chooses to exit.
    """
    # Define ANSI escape codes for colors
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    
    author_str = "Author: https://github.com/Issei-177013"

    # Embed ASCII art
    art = """

 ██████╗███████╗    ██╗   ██╗████████╗██╗██╗     ███████╗
██╔════╝██╔════╝    ██║   ██║╚══██╔══╝██║██║     ██╔════╝
██║     █████╗█████╗██║   ██║   ██║   ██║██║     ███████╗
██║     ██╔══╝╚════╝██║   ██║   ██║   ██║██║     ╚════██║
╚██████╗██║         ╚██████╔╝   ██║   ██║███████╗███████║
 ╚═════╝╚═╝          ╚═════╝    ╚═╝   ╚═╝╚══════╝╚══════╝
                                                              
"""
    
    while True:
        clear_screen()
        print_slow(f"{YELLOW}{art}{RESET}")
        print_slow(f"{CYAN}{author_str}{RESET}")
        print_slow(f"{CYAN}{version_str}{RESET}")
        
        print_slow(f"{CYAN}{HEADER_LINE}{RESET}")

        print_slow("\n--- Main Menu ---")
        print_slow("1. 👤 Manage Cloudflare Accounts")
        print_slow("2. 🌐 Manage Zones")
        print_slow("3. 📜 Manage DNS Records")
        print_slow("4. 🔄 IP Rotator Tools")
        print_slow("5. 📡 Traffic Monitoring")
        print_slow("6. 📄 View Application Logs")
        print_slow("7. ⚙️ Settings")
        print_slow("0. 🚪 Exit")
        print_slow(f"{CYAN}{OPTION_SEPARATOR}{RESET}")

        choice = input("👉 Enter your choice: ").strip()
        
        if choice == "1":
            account_management_menu()
        elif choice == "2":
            zone_management_menu()
        elif choice == "3":
            dns_management_menu()
        elif choice == "4":
            rotator_tools_menu()
        elif choice == "5":
            traffic_monitoring_menu()
        elif choice == "6":
            view_live_logs()
        elif choice == "7":
            settings_menu()
        elif choice == "0":
            if confirm_action("Are you sure you want to exit?"):
                logger.info("Exiting Cloudflare Utils Manager.")
                break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print_slow("❌ Invalid choice. Please select a valid option.")
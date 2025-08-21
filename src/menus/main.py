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
from ..display import *

def main_menu():
    """
    Displays and handles the main menu of the application.
    """
    author_str = "Author: https://github.com/Issei-177013"

    art_lines = [
        f" {COLOR_CF_ORANGE} ██████╗███████╗{RESET_COLOR}    {COLOR_CF_YELLOW}██╗   ██╗████████╗██╗██╗     ███████╗{RESET_COLOR}",
        f" {COLOR_CF_ORANGE}██╔════╝██╔════╝{RESET_COLOR}    {COLOR_CF_YELLOW}██║   ██║╚══██╔══╝██║██║     ██╔════╝{RESET_COLOR}",
        f" {COLOR_CF_ORANGE}██║     █████╗{RESET_COLOR}█████╗{COLOR_CF_YELLOW}██║   ██║   ██║   ██║██║     ███████╗{RESET_COLOR}",
        f" {COLOR_CF_ORANGE}██║     ██╔══╝{RESET_COLOR}╚════╝{COLOR_CF_YELLOW}██║   ██║   ██║   ██║██║     ╚════██║{RESET_COLOR}",
        f" {COLOR_CF_ORANGE}╚██████╗██║{RESET_COLOR}         {COLOR_CF_YELLOW}╚██████╔╝   ██║   ██║███████╗███████║{RESET_COLOR}",
        f"  {COLOR_CF_ORANGE}╚═════╝╚═╝{RESET_COLOR}          {COLOR_CF_YELLOW}╚═════╝    ╚═╝   ╚═╝╚══════╝╚══════╝{RESET_COLOR}"
    ]
    
    while True:
        clear_screen()
        print_fast("\n")
        for line in art_lines:
            print_fast(line)
        print_fast("\n")
        print_fast(f"{COLOR_INFO}{author_str}{RESET_COLOR}")
        print_fast(f"{COLOR_INFO}{version_str}{RESET_COLOR}")
        
        print_fast(f"{COLOR_SEPARATOR}{HEADER_LINE}{RESET_COLOR}")

        print_fast(f"\n{COLOR_TITLE}--- Main Menu ---{RESET_COLOR}")
        print_slow("1. 👤 Manage Cloudflare Accounts")
        print_slow("2. 🌐 Manage Zones")
        print_slow("3. 📜 Manage DNS Records")
        print_slow("4. 🔄 IP Rotator Tools")
        print_slow("5. 📡 Traffic Monitoring")
        print_slow("6. 📄 View Application Logs")
        print_slow("7. ⚙️ Settings")
        print_slow("0. 🚪 Exit")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

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
            print_fast(f"{COLOR_WARNING}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
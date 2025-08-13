import sys
import os

# Adjust path to import from root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
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

def main_menu():
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
        clear_screen() # Clear screen on each loop iteration
        print(f"{YELLOW}{art}{RESET}")
        # Print author and version after the art
        print(f"{CYAN}{author_str}{RESET}")
        print(f"{CYAN}{version_str}{RESET}")
        
        print("===================================")

        print("\n--- Main Menu ---")
        print("1. 👤 Manage Cloudflare Accounts")
        print("2. 🌐 Manage Zones")
        print("3. 📜 Manage DNS Records")
        print("4. 🔄 IP Rotator Tools")
        print("5. 📄 View Application Logs")
        print("6. ⚙️ Settings")
        print("0. 🚪 Exit")
        print("-----------------")

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
            view_live_logs()
        elif choice == "6":
            settings_menu()
        elif choice == "0":
            if confirm_action("Are you sure you want to exit?"):
                logger.info("Exiting Cloudflare Utils Manager.")
                break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print("❌ Invalid choice. Please select a valid option.")
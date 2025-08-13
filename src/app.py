import os
import sys
from .config import load_config
from .menus.main import main_menu
from .menus.accounts import add_account
from .menus.utils import clear_screen

def main():
    """The main function to run the application."""
    # Load configuration at the start
    config = load_config()

    # Check if any accounts are configured
    if not config.get("accounts"):
        clear_screen()
        print("👋 Welcome to Cloudflare Utils!")
        print("It looks like this is your first time, or you don't have any accounts configured yet.")
        print("Let's add your first Cloudflare account.")
        input("\nPress Enter to continue...")
        add_account()

        # After adding an account, check again. If still no account, exit.
        config = load_config()
        if not config.get("accounts"):
            print("\nNo account was added. Exiting.")
            sys.exit(0)

    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n👋 Exiting Cloudflare Utils Manager. Goodbye!")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
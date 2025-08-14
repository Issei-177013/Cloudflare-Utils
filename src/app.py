import os
import sys
from .config import load_config
from .logger import configure_console_logging
from .menus.main import main_menu
from .menus.accounts import add_account
from .menus.utils import clear_screen

def main():
    """
    The main entry point for the Cloudflare Utils application.

    This function initializes the application by:
    1. Loading the configuration.
    2. Configuring console logging.
    3. Checking if any Cloudflare accounts are set up. If not, it guides
       the user through adding their first account.
    4. Launching the main interactive menu.
    5. Handling a graceful exit on KeyboardInterrupt (Ctrl+C).
    """
    # Load configuration at the start
    config = load_config()

    # Configure console logging based on the loaded config
    configure_console_logging(config)

    # Check if any accounts are configured. If not, prompt the user to add one.
    if not config.get("accounts"):
        clear_screen()
        print("👋 Welcome to Cloudflare Utils!")
        print("It looks like this is your first time, or you don't have any accounts configured yet.")
        print("Let's add your first Cloudflare account.")
        input("\nPress Enter to continue...")
        add_account()

        # After attempting to add an account, reload the config and check again.
        config = load_config()
        if not config.get("accounts"):
            print("\nNo account was added. Exiting.")
            sys.exit(0)
    try:
        # Start the main interactive menu.
        main_menu()
    except KeyboardInterrupt:
        # Handle graceful shutdown on Ctrl+C.
        print("\n👋 Exiting Cloudflare Utils Manager. Goodbye!")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
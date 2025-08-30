#!/opt/Cloudflare-Utils/venv/bin/python
"""
Cloudflare Utils CLI Runner.

This script serves as the main entry point for the Cloudflare Utils command-line
interface (CLI). It ensures that the application is run with root privileges,
as required for managing configurations and system services (like cron jobs).

If the script is not run as root, it will exit with an error message.
"""

import os
import sys
import subprocess

def ensure_root():
    """
    Ensures the script is running with root privileges.

    Checks if the effective user ID is 0 (root). If not, it prints an
    error message and exits. This is a security measure to prevent
    unprivileged execution of commands that require root access.

    This function is critical for operations that require elevated permissions,
    such as creating global commands, managing system files, or setting up
    cron jobs during installation.
    """
    if os.geteuid() != 0:
        print("This script must be run as root. Please run the command with 'sudo'.")
        sys.exit(1)

if __name__ == "__main__":
    # Get the absolute path of the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Add the script's directory to the Python path
    sys.path.insert(0, script_dir)

    # Handle special flags that should run without the main app
    if '--restart-bot' in sys.argv:
        ensure_root()
        from src.core.service_manager import service_manager
        from src.core.config import config_manager
        
        config = config_manager.get_config()
        if config.get("bot", {}).get("enabled", False):
            print("Restarting Telegram bot service due to an update...")
            success, message = service_manager.restart_service()
            if success:
                print("Service restarted successfully.")
            else:
                print(f"Failed to restart service: {message}")
        else:
            # This case should ideally not be hit if the installer script checks first,
            # but it's here as a safeguard.
            print("Bot is not enabled, skipping restart.")
        sys.exit(0)

    # Ensure root privileges before importing and running the main application.
    ensure_root()
    
    # Import the necessary components
    from src.app import main
    from src.core.background_service import run_background_service
    import threading

    # Start the background service in a daemon thread
    service_thread = threading.Thread(target=run_background_service, daemon=True)
    service_thread.start()

    # Run the main application logic
    main()
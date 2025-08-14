#!/usr/bin/env python3
"""
Cloudflare Utils CLI Runner.

This script serves as the main entry point for the Cloudflare Utils command-line
interface (CLI). It ensures that the application is run with root privileges,
as required for managing configurations and system services (like cron jobs).

If the script is not run as root, it attempts to re-launch itself using `sudo`
to elevate privileges.
"""

import os
import sys
import subprocess

def ensure_root():
    """
    Ensures the script is running with root privileges.

    Checks if the effective user ID is 0 (root). If not, it attempts to
    re-execute the script with `sudo`. If `sudo` fails or is not found,
    it prints an error message and exits.

    This function is critical for operations that require elevated permissions,
    such as creating global commands, managing system files, or setting up
    cron jobs during installation.
    """
    if os.geteuid() != 0:
        print("This script must be run as root. Attempting to elevate privileges...")
        try:
            # Relaunch the script with sudo to gain root access.
            subprocess.check_call(['sudo', sys.executable] + sys.argv)
            # Exit the original non-elevated process successfully.
            sys.exit(0)
        except subprocess.CalledProcessError:
            print("\nFailed to gain root access. Please run the command with 'sudo'.")
            sys.exit(1)
        except FileNotFoundError:
            print("\n`sudo` is required to elevate privileges but was not found.")
            print("Please run this script as root.")
            sys.exit(1)

if __name__ == "__main__":
    # Ensure root privileges before importing and running the main application.
    ensure_root()
    # Import the main application logic only after root access is confirmed.
    from src.app import main
    main()
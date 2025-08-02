#!/usr/bin/env python3
import os
import sys
import subprocess

def ensure_root():
    """Ensures the script is running as root, elevating with sudo if necessary."""
    if os.geteuid() != 0:
        print("This script must be run as root. Attempting to elevate privileges...")
        try:
            # Relaunch the script with sudo
            subprocess.check_call(['sudo', sys.executable] + sys.argv)
            # Exit the original non-elevated process
            sys.exit(0)
        except subprocess.CalledProcessError:
            print(f"\nFailed to gain root access. Please run the command with 'sudo'.")
            sys.exit(1)
        except FileNotFoundError:
            print("\n`sudo` is required to elevate privileges but was not found.")
            print("Please run this script as root.")
            sys.exit(1)

if __name__ == "__main__":
    ensure_root()
    # Import the main application logic only after ensuring root privileges
    from src.app import main
    main()
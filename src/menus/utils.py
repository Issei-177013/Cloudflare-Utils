import os
import time
from ..logger import logger, LOGS_DIR

def clear_screen():
    """Clears the terminal screen."""
    # For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # For macOS and Linux
    else:
        _ = os.system('clear')


def select_from_list(items, prompt):
    """Displays a numbered list of items and returns the selected item."""
    if not items:
        print("No items to select.")
        return None

    print(prompt)
    for i, item in enumerate(items):
        # Assuming item is a dictionary and has a 'name' or 'domain' key
        name = item.get('name', item.get('domain', 'Unknown Item'))
        print(f"{i+1}. {name}")

    while True:
        try:
            choice = int(input("Enter your choice (number): "))
            if 1 <= choice <= len(items):
                return items[choice-1]
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def confirm_action(prompt="Are you sure you want to proceed?"):
    """Asks for user confirmation."""
    while True:
        response = input(f"{prompt} (yes/no): ").strip().lower()
        if response in ["yes", "y"]:
            return True
        elif response in ["no", "n"]:
            return False
        else:
            print("❌ Invalid input. Please enter 'yes' or 'no'.")


def view_live_logs(record_name=None):
    """
    Displays historical and live logs from the application log file.
    Optionally filters for a specific record.
    """
    clear_screen()
    if record_name:
        print(f"\n--- Live Logs for: {record_name} ---")
    else:
        print("\n--- Live Application Logs ---")
    print("Press Ctrl+C to stop viewing.")

    log_file_path = os.path.join(LOGS_DIR, "app.log")
    
    try:
        with open(log_file_path, 'r') as f:
            # --- Display historical logs ---
            for line in f:
                if not record_name or record_name in line:
                    print(line, end='')
            
            # --- Wait for new logs ---
            print("\n--- Waiting for new logs... ---")
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                if not record_name or record_name in line:
                    print(line, end='')

    except FileNotFoundError:
        print("Log file not found. Logging may not be configured yet.")
        input("\nPress Enter to return...")
    except KeyboardInterrupt:
        print("\n--- Stopped viewing logs. ---")
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        print(f"An error occurred while trying to read the log file: {e}")
        input("\nPress Enter to return...")
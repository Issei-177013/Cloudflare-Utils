import os
import time
from ..logger import logger, LOGS_DIR
from ..display import *
from ..input_helper import get_user_input, get_rotation_interval

def get_schedule_config():
    """
    Asks the user to configure a rotation schedule (time-based or trigger-based).
    Returns a schedule dictionary or None if cancelled.
    """
    print_fast("\n--- Configure Rotation Schedule ---")
    print_slow("1. Time-based (e.g., every 30 minutes)")
    print_slow("2. Trigger-based (e.g., when traffic exceeds a limit)")
    print_slow("0. Cancel")
    
    choice = get_user_input("Enter your choice: ")

    if choice == '1':
        interval = get_rotation_interval()
        return {"type": "time", "interval_minutes": interval}
    elif choice == '2':
        from ..triggers import select_trigger
        trigger_id = select_trigger()
        if trigger_id:
            return {"type": "trigger", "trigger_id": trigger_id}
        else:
            return None # User cancelled trigger selection
    else:
        return None

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
        print_fast(f"{COLOR_WARNING}No items to select.{RESET_COLOR}")
        return None

    print_fast(prompt)
    for i, item in enumerate(items):
        # Assuming item is a dictionary and has a 'name' or 'domain' key
        name = item.get('name', item.get('domain', 'Unknown Item'))
        print_slow(f"{i+1}. {name}")

    while True:
        try:
            choice = int(input("Enter your choice (number): "))
            if 1 <= choice <= len(items):
                return items[choice-1]
            else:
                print_fast(f"{COLOR_ERROR}Invalid choice. Please enter a number from the list.{RESET_COLOR}")
        except ValueError:
            print_fast(f"{COLOR_ERROR}Invalid input. Please enter a number.{RESET_COLOR}")


def confirm_action(prompt="Are you sure you want to proceed?"):
    """Asks for user confirmation."""
    while True:
        response = input(f"{prompt} (yes/no): ").strip().lower()
        if response in ["yes", "y"]:
            return True
        elif response in ["no", "n"]:
            return False
        else:
            print_fast(f"{COLOR_ERROR}❌ Invalid input. Please enter 'yes' or 'no'.{RESET_COLOR}")


def view_live_logs(record_name=None):
    """
    Displays historical and live logs from the application log file.
    Optionally filters for a specific record.
    """
    clear_screen()
    if record_name:
        print_fast(f"\n--- Live Logs for: {record_name} ---")
    else:
        print_fast("\n--- Live Application Logs ---")
    print_fast("Press Ctrl+C to stop viewing.")

    log_file_path = os.path.join(LOGS_DIR, "app.log")
    
    try:
        with open(log_file_path, 'r') as f:
            # --- Display historical logs ---
            for line in f:
                if not record_name or record_name in line:
                    print_fast(line, end='')
            
            # --- Wait for new logs ---
            print_fast("\n--- Waiting for new logs... ---")
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                if not record_name or record_name in line:
                    print_fast(line, end='')

    except FileNotFoundError:
        print_fast(f"{COLOR_WARNING}Log file not found. Logging may not be configured yet.{RESET_COLOR}")
        input("\nPress Enter to return...")
    except KeyboardInterrupt:
        print_fast("\n--- Stopped viewing logs. ---")
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        print_fast(f"{COLOR_ERROR}An error occurred while trying to read the log file: {e}{RESET_COLOR}")
        input("\nPress Enter to return...")


def parse_selection(selection_str, max_value):
    """
    Parses a selection string (e.g., "1,3-5,7") into a list of indices.
    """
    indices = set()
    parts = selection_str.replace(" ", "").split(',')
    for part in parts:
        if not part:
            continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start > end:
                    start, end = end, start # handle reverse ranges
                if 1 <= start <= max_value and 1 <= end <= max_value:
                    for i in range(start, end + 1):
                        indices.add(i - 1)
                else:
                    raise ValueError("Range out of bounds.")
            except ValueError:
                raise ValueError(f"Invalid range '{part}'.")
        else:
            try:
                index = int(part)
                if 1 <= index <= max_value:
                    indices.add(index - 1)
                else:
                    raise ValueError(f"Index {index} is out of bounds.")
            except ValueError:
                raise ValueError(f"Invalid selection '{part}'.")
    return sorted(list(indices))
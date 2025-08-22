import os
import time
from ..core.logger import logger
from ..core.validator import is_valid_ipv4, is_valid_ipv6
from ..display import *

# Note: LOGS_DIR is imported here because it's used by view_live_logs,
# which is a UI function.
from ..core.logger import LOGS_DIR

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
        from .trigger_management import select_trigger
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

def _get_sanitized_input(prompt):
    """
    Gets sanitized user input from the console.
    Strips leading/trailing whitespace.
    """
    user_input = input(prompt)
    # Sanitize the input to remove any invalid characters that might cause encoding errors
    return user_input.encode('utf-8', 'ignore').decode('utf-8').strip()

def get_validated_input(prompt, validation_func, error_message, allow_empty=False):
    """
    Prompts the user for input and validates it using the provided validation function.
    If validation fails, it prints the error message and retries.
    """
    while True:
        user_input = _get_sanitized_input(prompt)
        if allow_empty and user_input == "":
            return user_input
            
        if validation_func(user_input):
            return user_input
        else:
            logger.warning(f"Validation failed for input: '{user_input}' using function: {validation_func.__name__}")
            print(f"❌ {error_message}")

def get_ip_list(record_type):
    """
    Prompts the user for a comma-separated list of IP addresses and validates them.
    """
    prompt = f"Enter IPs for {record_type} record (comma separated): "
    error_message = "Invalid IP address found in the list."
    
    while True:
        ip_list_str = _get_sanitized_input(prompt)
        ips = [ip.strip() for ip in ip_list_str.split(',')]
        
        is_valid = True
        validation_func = is_valid_ipv4 if record_type == 'A' else is_valid_ipv6
        
        for ip in ips:
            if not validation_func(ip):
                logger.warning(f"Invalid {record_type} IP: {ip}")
                print(f"❌ Invalid IP: '{ip}'. Please enter valid {record_type} addresses.")
                is_valid = False
                break
        
        if is_valid:
            return ips

def get_record_type():
    """
    Prompts the user for a DNS record type and validates it.
    """
    prompt = "Record type (A/AAAA): "
    error_message = "Invalid record type. Please enter 'A' or 'AAAA'."
    
    while True:
        rec_type = _get_sanitized_input(prompt).upper()
        if rec_type in ['A', 'AAAA']:
            return rec_type
        else:
            logger.warning(f"Invalid record type entered: {rec_type}")
            print(f"❌ {error_message}")

def get_rotation_interval(optional=False):
    """
    Prompts the user for a rotation interval and validates it.
    """
    prompt = "Rotation interval in minutes (min 5, default 30): "
    if optional:
        prompt = "Enter new interval (minutes, min 5) or press Enter to keep current: "
        
    while True:
        interval_str = _get_sanitized_input(prompt)
        if not interval_str:
            return 30 if not optional else None
            
        try:
            interval = int(interval_str)
            if interval >= 5:
                return interval
            else:
                logger.warning(f"Rotation interval too low: {interval}")
                print("❌ Rotation interval must be at least 5 minutes.")
        except ValueError:
            logger.warning(f"Invalid interval input: {interval_str}")
            print("❌ Invalid input. Please enter a number.")

def get_zone_type():
    """
    Prompts the user for a zone type and validates it.
    """
    prompt = "Zone type (full/partial, default: full): "
    error_message = "Invalid zone type. Please enter 'full' or 'partial'."
    
    while True:
        zone_type = _get_sanitized_input(prompt).lower()
        if zone_type in ['full', 'partial', '']:
            return zone_type or 'full'
        else:
            logger.warning(f"Invalid zone type entered: {zone_type}")
            print(f"❌ {error_message}")

def get_user_input(prompt, default=None):
    """
    Prompts the user for input. If a default is provided, it returns the default
    when the user enters empty input. Otherwise, it ensures the input is not empty.
    """
    while True:
        user_input = _get_sanitized_input(prompt)
        if user_input:
            return user_input
        if default is not None:
            return default
        
        print("❌ Input cannot be empty.")

def get_numeric_input(prompt, num_type, default=None, min_val=None, max_val=None):
    """
    Prompts for a numeric value, with optional default, type, and range validation.
    """
    while True:
        user_input = _get_sanitized_input(prompt)
        if not user_input and default is not None:
            return default
        
        try:
            num_value = num_type(user_input)
            
            if min_val is not None and num_value < min_val:
                print(f"❌ Value must be at least {min_val}.")
                continue
            
            if max_val is not None and num_value > max_val:
                print(f"❌ Value must be no more than {max_val}.")
                continue
                
            return num_value
        except ValueError:
            print(f"❌ Invalid input. Please enter a valid number ({num_type.__name__}).")
from .validator import is_valid_ipv4, is_valid_ipv6
from .logger import input_helper_logger

def get_validated_input(prompt, validation_func, error_message):
    """
    Prompts the user for input and validates it using the provided validation function.
    If validation fails, it prints the error message and retries.
    """
    while True:
        user_input = input(prompt).strip()
        if validation_func(user_input):
            return user_input
        else:
            input_helper_logger.warning(f"Validation failed for input: '{user_input}' using function: {validation_func.__name__}")
            print(f"❌ {error_message}")

def get_ip_list(record_type):
    """
    Prompts the user for a comma-separated list of IP addresses and validates them.
    """
    prompt = f"Enter IPs for {record_type} record (comma separated): "
    error_message = "Invalid IP address found in the list."
    
    while True:
        ip_list_str = input(prompt).strip()
        ips = [ip.strip() for ip in ip_list_str.split(',')]
        
        is_valid = True
        validation_func = is_valid_ipv4 if record_type == 'A' else is_valid_ipv6
        
        for ip in ips:
            if not validation_func(ip):
                input_helper_logger.warning(f"Invalid {record_type} IP: {ip}")
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
        rec_type = input(prompt).strip().upper()
        if rec_type in ['A', 'AAAA']:
            return rec_type
        else:
            input_helper_logger.warning(f"Invalid record type entered: {rec_type}")
            print(f"❌ {error_message}")

def get_rotation_interval():
    """
    Prompts the user for a rotation interval and validates it.
    """
    prompt = "Rotation interval in minutes (min 5, default 30): "
    
    while True:
        interval_str = input(prompt).strip()
        if not interval_str:
            return 30  # Default value
            
        try:
            interval = int(interval_str)
            if interval >= 5:
                return interval
            else:
                input_helper_logger.warning(f"Rotation interval too low: {interval}")
                print("❌ Rotation interval must be at least 5 minutes.")
        except ValueError:
            input_helper_logger.warning(f"Invalid interval input: {interval_str}")
            print("❌ Invalid input. Please enter a number.")

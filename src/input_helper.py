from .validator import is_valid_ipv4, is_valid_ipv6
from .logger import logger

def get_validated_input(prompt, validation_func, error_message, allow_empty=False):
    """
    Prompts the user for input and validates it using the provided validation function.
    If validation fails, it prints the error message and retries.
    """
    while True:
        user_input = input(prompt).strip()
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
        ip_list_str = input(prompt).strip()
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
        rec_type = input(prompt).strip().upper()
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
        interval_str = input(prompt).strip()
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
        zone_type = input(prompt).strip().lower()
        if zone_type in ['full', 'partial', '']:
            return zone_type or 'full'
        else:
            logger.warning(f"Invalid zone type entered: {zone_type}")
            print(f"❌ {error_message}")
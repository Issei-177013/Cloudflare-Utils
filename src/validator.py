import re

def is_valid_ipv4(ip):
    """Validate IPv4 addresses."""
    pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    if pattern.match(ip):
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    return False

def is_valid_ipv6(ip):
    """Validate IPv6 addresses."""
    pattern = re.compile(r"^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$", re.IGNORECASE)
    return pattern.match(ip) is not None

def is_valid_domain(domain):
    """Validate a domain name."""
    # Basic domain validation regex
    pattern = re.compile(
        r'^(?:[a-zA-Z0-9]'  # First character of the domain
        r'(?:[a-zA-Z0-9-_]{0,61}[a-zA-Z0-9])?\.)'  # Subdomain
        r'+[a-zA-Z]{2,6}$'  # Top-level domain
    )
    return pattern.match(domain) is not None

def is_valid_zone_id(zone_id):
    """Validate a Cloudflare Zone ID."""
    # 32-character hexadecimal string
    pattern = re.compile(r'^[a-f0-9]{32}$')
    return pattern.match(zone_id) is not None

def is_valid_record_name(name):
    """Validate a DNS record name."""
    # This is a basic check, can be improved for more complex FQDN rules
    return isinstance(name, str) and len(name) > 0

def is_valid_record_type(record_type):
    """Validate a DNS record type."""
    return record_type in ['A', 'AAAA']

def validate_record(record):
    """Validate a single DNS record."""
    if 'name' not in record or not isinstance(record['name'], str) or not record['name']:
        raise ValueError("Record 'name' is required and must be a non-empty string.")
    
    if 'type' not in record or record['type'] not in ['A', 'AAAA']:
        raise ValueError("Record 'type' must be 'A' or 'AAAA'.")
    
    if 'ips' not in record or not isinstance(record['ips'], list) or not record['ips']:
        raise ValueError("Record 'ips' is required and must be a non-empty list.")
    
    for ip in record['ips']:
        if record['type'] == 'A' and not is_valid_ipv4(ip):
            raise ValueError(f"Invalid IPv4 address in record '{record['name']}': {ip}")
        elif record['type'] == 'AAAA' and not is_valid_ipv6(ip):
            raise ValueError(f"Invalid IPv6 address in record '{record['name']}': {ip}")
            
    if 'rotation_interval_minutes' in record and (not isinstance(record['rotation_interval_minutes'], int) or record['rotation_interval_minutes'] < 5):
        raise ValueError("Rotation interval must be an integer of at least 5.")
        
    return True

def validate_zone(zone):
    """Validate a single zone."""
    if 'domain' not in zone or not isinstance(zone['domain'], str) or not zone['domain']:
        raise ValueError("Zone 'domain' is required and must be a non-empty string.")
    
    if 'zone_id' not in zone or not isinstance(zone['zone_id'], str) or not zone['zone_id']:
        raise ValueError("Zone 'zone_id' is required and must be a non-empty string.")
    
    if 'records' not in zone or not isinstance(zone['records'], list):
        raise ValueError("Zone 'records' must be a list.")
        
    for record in zone['records']:
        validate_record(record)
        
    return True

def validate_account(account):
    """Validate a single account."""
    if 'name' not in account or not isinstance(account['name'], str) or not account['name']:
        raise ValueError("Account 'name' is required and must be a non-empty string.")
    # TODO: Validate with Connectivity Check 
    if 'api_token' not in account or not isinstance(account['api_token'], str) or not account['api_token']:
        raise ValueError("Account 'api_token' is required and must be a non-empty string.")
        
    if 'zones' not in account or not isinstance(account['zones'], list):
        raise ValueError("Account 'zones' must be a list.")
        
    for zone in account['zones']:
        validate_zone(zone)
        
    return True

def validate_config(data):
    """Validate the entire configuration data."""
    if 'accounts' not in data or not isinstance(data['accounts'], list):
        raise ValueError("Top-level 'accounts' key must be a list.")
        
    for account in data['accounts']:
        validate_account(account)
        
    return True

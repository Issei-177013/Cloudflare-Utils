"""
Input and Configuration Validators.

This module provides a collection of functions for validating various types of
data used throughout the application, including IP addresses, domain names, and
the structure of the main configuration file.
"""
import re

def is_valid_ipv4(ip):
    """
    Validates an IPv4 address.

    Args:
        ip (str): The string to validate as an IPv4 address.

    Returns:
        bool: True if the string is a valid IPv4 address, False otherwise.
    """
    pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    if pattern.match(ip):
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    return False

def is_valid_ipv6(ip):
    """
    Validates an IPv6 address.

    Args:
        ip (str): The string to validate as an IPv6 address.

    Returns:
        bool: True if the string is a valid IPv6 address, False otherwise.
    """
    pattern = re.compile(r"^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$", re.IGNORECASE)
    return pattern.match(ip) is not None

def is_valid_domain(domain):
    """
    Validates a domain name using a basic regex.

    Args:
        domain (str): The domain name string to validate.

    Returns:
        bool: True if the string is a valid domain name, False otherwise.
    """
    pattern = re.compile(
        r'^(?:[a-zA-Z0-9]'
        r'(?:[a-zA-Z0-9-_]{0,61}[a-zA-Z0-9])?\.)'
        r'+[a-zA-Z]{2,6}$'
    )
    return pattern.match(domain) is not None

def is_valid_zone_id(zone_id):
    """
    Validates a Cloudflare Zone ID.

    Args:
        zone_id (str): The Zone ID string to validate.

    Returns:
        bool: True if the string is a valid 32-character hex Zone ID, False otherwise.
    """
    pattern = re.compile(r'^[a-f0-9]{32}$')
    return pattern.match(zone_id) is not None

def is_valid_record_name(name):
    """
    Validates a DNS record name.

    Args:
        name (str): The DNS record name to validate.

    Returns:
        bool: True if the name is a non-empty string, False otherwise.
    """
    return isinstance(name, str) and len(name) > 0

def is_valid_rotator_record_type(record_type):
    """
    Validates that a DNS record type is valid for the IP rotator ('A' or 'AAAA').

    Args:
        record_type (str): The record type to validate.

    Returns:
        bool: True if the type is 'A' or 'AAAA', False otherwise.
    """
    return record_type.upper() in ['A', 'AAAA']

def is_valid_dns_record_type(record_type):
    """
    Validates a general DNS record type against a list of common types.

    Args:
        record_type (str): The record type to validate.

    Returns:
        bool: True if the type is a known common type, False otherwise.
    """
    common_types = [
        'A', 'AAAA', 'CNAME', 'TXT', 'MX', 'SRV', 'SPF', 'DKIM', 'DMARC',
        'NS', 'SOA', 'PTR', 'CAA', 'DS', 'DNSKEY', 'NAPTR', 'LOC'
    ]
    return record_type.upper() in common_types

def validate_record(record):
    """
    Validates the structure and content of a single DNS record configuration.

    Args:
        record (dict): The record dictionary from the configuration.

    Returns:
        bool: True if the record is valid.

    Raises:
        ValueError: If any part of the record configuration is invalid.
    """
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
    """
    Validates the structure and content of a single zone configuration.

    Args:
        zone (dict): The zone dictionary from the configuration.

    Returns:
        bool: True if the zone is valid.

    Raises:
        ValueError: If any part of the zone configuration is invalid.
    """
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
    """
    Validates the structure and content of a single account configuration.

    Args:
        account (dict): The account dictionary from the configuration.

    Returns:
        bool: True if the account is valid.

    Raises:
        ValueError: If any part of the account configuration is invalid.
    """
    if 'name' not in account or not isinstance(account['name'], str) or not account['name']:
        raise ValueError("Account 'name' is required and must be a non-empty string.")
    if 'api_token' not in account or not isinstance(account['api_token'], str) or not account['api_token']:
        raise ValueError("Account 'api_token' is required and must be a non-empty string.")
        
    if 'zones' not in account or not isinstance(account['zones'], list):
        raise ValueError("Account 'zones' must be a list.")
        
    for zone in account['zones']:
        validate_zone(zone)
        
    return True

def validate_config(data):
    """
    Validates the entire configuration data structure.

    Args:
        data (dict): The full configuration dictionary to validate.

    Returns:
        bool: True if the entire configuration is valid.

    Raises:
        ValueError: If any part of the configuration is invalid.
    """
    if 'accounts' not in data or not isinstance(data['accounts'], list):
        raise ValueError("Top-level 'accounts' key must be a list.")
        
    for account in data['accounts']:
        validate_account(account)
        
    return True

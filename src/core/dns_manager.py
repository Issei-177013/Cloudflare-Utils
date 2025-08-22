"""
DNS and Account Configuration Management.

This module provides functions for managing DNS records, rotation groups, and
Cloudflare accounts within the local `configs.json` file. These functions
handle the business logic for adding, editing, and deleting configuration
entries, abstracting the direct manipulation of the configuration file.

All functions operate on the local configuration and do not directly interact
with the Cloudflare API.
"""
from .config import config_manager
from .validator import is_valid_rotator_record_type
from .logger import logger
from .exceptions import ConfigError, InvalidInputError

def add_record(account_name, zone_domain, record_name, record_type, ips, schedule):
    """
    Adds a new DNS record configuration for IP rotation.

    Args:
        account_name (str): The name of the Cloudflare account.
        zone_domain (str): The domain of the zone for the record.
        record_name (str): The name of the DNS record.
        record_type (str): The type of the record ('A' or 'AAAA').
        ips (list): A list of IP addresses for rotation.
        schedule (dict or None): The schedule configuration object.
    
    Returns:
        bool: True if the record was added successfully.

    Raises:
        InvalidInputError: If input parameters are invalid.
        ConfigError: If the record already exists or an entity is not found.
    """
    if not is_valid_rotator_record_type(record_type):
        raise InvalidInputError(f"Invalid record type '{record_type}'. Must be 'A' or 'AAAA'.")
    
    acc = config_manager.find_account(account_name)
    if not acc:
        raise ConfigError(f"Account '{account_name}' not found.")

    zone = config_manager.find_zone(acc, zone_domain)
    if not zone:
        # If zone doesn't exist, create it
        zone = {"domain": zone_domain, "records": [], "rotation_groups": []}
        acc["zones"].append(zone)

    if config_manager.find_record(zone, record_name):
        raise ConfigError(f"Record '{record_name}' already exists in zone '{zone_domain}'.")

    record_data = {
        "name": record_name,
        "type": record_type,
        "ips": ips,
    }
    if schedule:
        record_data["schedule"] = schedule

    zone["records"].append(record_data)
    config_manager.save_config()
    logger.info(f"Record '{record_name}' added to zone '{zone_domain}'.")
    return True

def delete_record(account_name, zone_domain, record_name):
    """
    Deletes a DNS record configuration.

    Args:
        account_name (str): The name of the Cloudflare account.
        zone_domain (str): The domain of the zone for the record.
        record_name (str): The name of the DNS record to delete.

    Returns:
        bool: True if the record was deleted successfully.

    Raises:
        ConfigError: If the account, zone, or record is not found.
    """
    acc = config_manager.find_account(account_name)
    if not acc:
        raise ConfigError(f"Account '{account_name}' not found.")

    zone = config_manager.find_zone(acc, zone_domain)
    if not zone:
        raise ConfigError(f"Zone '{zone_domain}' not found in account '{account_name}'.")

    record_to_delete = config_manager.find_record(zone, record_name)
    if not record_to_delete:
        raise ConfigError(f"Record '{record_name}' not found in zone '{zone_domain}'.")

    zone["records"].remove(record_to_delete)
    config_manager.save_config()
    logger.info(f"Record '{record_to_delete['name']}' deleted successfully from local configuration.")
    return True


def edit_record(account_name, zone_domain, record_name, new_ips, new_type, new_interval):
    """
    Edits an existing DNS record configuration.

    Args:
        account_name (str): The name of the Cloudflare account.
        zone_domain (str): The domain of the zone for the record.
        record_name (str): The name of the DNS record to edit.
        new_ips (list or None): A new list of IPs, or None to keep existing.
        new_type (str or None): A new record type, or None to keep existing.
        new_interval (str or None): A new rotation interval, or None to keep existing.
                                     Use 'none' to remove the interval.

    Returns:
        bool: True if the record was edited successfully.

    Raises:
        ConfigError: If the account, zone, or record is not found.
        InvalidInputError: If new values are invalid.
    """
    acc = config_manager.find_account(account_name)
    if not acc:
        raise ConfigError(f"Account '{account_name}' not found.")

    zone = config_manager.find_zone(acc, zone_domain)
    if not zone:
        raise ConfigError(f"Zone '{zone_domain}' not found in account '{account_name}'.")

    record_to_edit = config_manager.find_record(zone, record_name)
    if not record_to_edit:
        raise ConfigError(f"Record '{record_name}' not found in zone '{zone_domain}'.")

    if new_ips:
        record_to_edit['ips'] = new_ips
    if new_type:
        if is_valid_rotator_record_type(new_type):
            record_to_edit['type'] = new_type
        else:
            raise InvalidInputError(f"Invalid record type '{new_type}'.")
            
    if new_interval is not None:
        if new_interval.lower() == 'none':
            if 'rotation_interval_minutes' in record_to_edit:
                del record_to_edit['rotation_interval_minutes']
        else:
            try:
                interval = int(new_interval)
                if interval < 5:
                    raise InvalidInputError("Rotation interval must be at least 5 minutes.")
                else:
                    record_to_edit['rotation_interval_minutes'] = interval
            except ValueError:
                raise InvalidInputError("Invalid input for interval. Must be a number or 'none'.")

    config_manager.save_config()
    logger.info(f"Record '{record_to_edit['name']}' updated successfully.")
    return True

def edit_account_in_config(account_name, new_name, new_token):
    """
    Edits the details of a Cloudflare account in the configuration.

    Args:
        account_name (str): The current name of the account to edit.
        new_name (str or None): The new name for the account, or None to keep existing.
        new_token (str or None): The new API token, or None to keep existing.
    
    Returns:
        bool: True if the account was edited successfully.

    Raises:
        ConfigError: If the account is not found.
    """
    acc = config_manager.find_account(account_name)
    if not acc:
        raise ConfigError(f"Account '{account_name}' not found.")

    if new_name:
        acc['name'] = new_name
    if new_token:
        acc['api_token'] = new_token

    config_manager.save_config()
    logger.info(f"Account '{account_name}' updated successfully.")
    return True

def delete_account_from_config(account_name):
    """
    Deletes a Cloudflare account from the configuration.

    Args:
        account_name (str): The name of the account to delete.

    Returns:
        bool: True if the account was deleted successfully.

    Raises:
        ConfigError: If the account is not found.
    """
    config_data = config_manager.get_config()
    acc = config_manager.find_account(account_name)
    if not acc:
        raise ConfigError(f"Account '{account_name}' not found.")

    config_data['accounts'].remove(acc)
    config_manager.save_config()
    logger.info(f"Account '{account_name}' deleted successfully.")
    return True


def add_rotation_group(account_name, zone_domain, group_name, record_names, schedule):
    """
    Adds a new rotation group to the configuration.

    A rotation group defines a set of DNS records within a zone whose IPs
    will be rotated among themselves.

    Args:
        account_name (str): The name of the Cloudflare account.
        zone_domain (str): The domain of the zone.
        group_name (str): The name for the new rotation group.
        record_names (list): A list of record names to include in the group.
        schedule (dict): The schedule configuration object.

    Returns:
        bool: True if the group was added successfully.

    Raises:
        ConfigError: If account/zone not found, or group already exists.
    """
    acc = config_manager.find_account(account_name)
    if not acc:
        raise ConfigError(f"Account '{account_name}' not found.")

    zone = config_manager.find_zone(acc, zone_domain)
    if not zone:
        raise ConfigError(f"Zone '{zone_domain}' not found in account '{account_name}'. Please add at least one single record to it first.")

    if "rotation_groups" not in zone:
        zone["rotation_groups"] = []

    if config_manager.find_rotation_group(zone, group_name):
        raise ConfigError(f"Rotation group '{group_name}' already exists in zone '{zone_domain}'.")

    group_data = {
        "name": group_name,
        "records": record_names,
        "schedule": schedule
    }

    zone["rotation_groups"].append(group_data)
    config_manager.save_config()
    logger.info(f"Rotation group '{group_name}' added to zone '{zone_domain}'.")
    return True

def edit_rotation_group(account_name, zone_domain, group_name, new_record_names, new_interval):
    """
    Edits an existing rotation group.

    Args:
        account_name (str): The name of the Cloudflare account.
        zone_domain (str): The domain of the zone.
        group_name (str): The name of the group to edit.
        new_record_names (list or None): A new list of record names, or None to keep existing.
        new_interval (str or None): A new rotation interval, or None to keep existing.
                                     Use 'none' to remove the interval.

    Returns:
        bool: True if the group was edited successfully.

    Raises:
        ConfigError: If account, zone, or group not found.
        InvalidInputError: If new values are invalid.
    """
    acc = config_manager.find_account(account_name)
    if not acc:
        raise ConfigError(f"Account '{account_name}' not found.")

    zone = config_manager.find_zone(acc, zone_domain)
    if not zone:
        raise ConfigError(f"Zone '{zone_domain}' not found.")

    group_to_edit = config_manager.find_rotation_group(zone, group_name)
    if not group_to_edit:
        raise ConfigError(f"Rotation group '{group_name}' not found.")

    if new_record_names:
        group_to_edit['records'] = new_record_names
        
    if new_interval is not None:
        if new_interval.lower() == 'none':
            if 'rotation_interval_minutes' in group_to_edit:
                 del group_to_edit['rotation_interval_minutes']
        else:
            try:
                interval = int(new_interval)
                if interval < 5:
                    raise InvalidInputError("Rotation interval must be at least 5 minutes.")
                else:
                    group_to_edit['rotation_interval_minutes'] = interval
            except ValueError:
                raise InvalidInputError("Invalid input for interval. Must be a number or 'none'.")

    config_manager.save_config()
    logger.info(f"Rotation group '{group_name}' updated successfully.")
    return True

def delete_rotation_group(account_name, zone_domain, group_name):
    """
    Deletes a rotation group from the configuration.

    Args:
        account_name (str): The name of the Cloudflare account.
        zone_domain (str): The domain of the zone.
        group_name (str): The name of the group to delete.

    Returns:
        bool: True if the group was deleted successfully.

    Raises:
        ConfigError: If the account, zone, or group is not found.
    """
    acc = config_manager.find_account(account_name)
    if not acc:
        raise ConfigError(f"Account '{account_name}' not found.")

    zone = config_manager.find_zone(acc, zone_domain)
    if not zone:
        raise ConfigError(f"Zone '{zone_domain}' not found.")

    group_to_delete = config_manager.find_rotation_group(zone, group_name)
    if not group_to_delete:
        raise ConfigError(f"Rotation group '{group_name}' not found.")

    zone["rotation_groups"].remove(group_to_delete)
    config_manager.save_config()
    logger.info(f"Rotation group '{group_name}' deleted successfully.")
    return True
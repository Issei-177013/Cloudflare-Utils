"""
Configuration Management.

This module is responsible for handling the application's configuration,
which is stored in JSON files. It provides functions for loading, saving,
and validating the main configuration (`configs.json`), as well as managing
the rotation status file (`rotation_status.json`).

The module also defines constants for configuration paths and default values.
"""
import json
import os
from .validator import validate_config
from .logger import logger

# Determine the absolute path to the directory where this script is located.
# This ensures that config files are found relative to the script's location,
# which is crucial for a consistent file structure, especially when installed globally.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "configs.json")
ROTATION_STATUS_PATH = os.path.join(SCRIPT_DIR, "rotation_status.json")

DEFAULT_ROTATION_INTERVAL_MINUTES = 30

def load_config():
    """
    Loads the main configuration from the `configs.json` file.

    If the file does not exist, it creates a default configuration structure
    and saves it. If the file is corrupted or cannot be decoded, it logs an
    error and returns a default configuration to prevent crashes.

    Returns:
        dict: The configuration data.
    """
    if not os.path.exists(CONFIG_PATH):
        logger.info(f"Config file not found at {CONFIG_PATH}. Creating a new one.")
        default_config = {"accounts": [], "settings": {"console_logging": True}}
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            # Ensure default settings exist to prevent key errors elsewhere.
            if "settings" not in config:
                config["settings"] = {"console_logging": True}
            elif "console_logging" not in config["settings"]:
                config["settings"]["console_logging"] = True
            return config
    except json.JSONDecodeError:
        logger.error(f"Could not decode JSON from {CONFIG_PATH}. Returning default config.")
        return {"accounts": [], "settings": {"console_logging": True}}

def validate_and_save_config(data):
    """
    Validates the configuration data and saves it to `configs.json`.

    Args:
        data (dict): The configuration data to validate and save.

    Returns:
        bool: True if the configuration was valid and saved successfully,
              False otherwise.
    """
    try:
        validate_config(data)
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        return False

def save_config(data):
    """
    Saves the configuration data to the `configs.json` file.

    This is a convenience wrapper around `validate_and_save_config`.

    Args:
        data (dict): The configuration data to save.
    """
    validate_and_save_config(data)

def find_account(data, account_name):
    """
    Finds an account by its name in the configuration data.

    Args:
        data (dict): The configuration data.
        account_name (str): The name of the account to find.

    Returns:
        dict or None: The account object if found, otherwise None.
    """
    for acc in data.get("accounts", []):
        if acc.get("name") == account_name:
            return acc
    return None

def find_zone(account_data, zone_domain):
    """
    Finds a zone by its domain name within an account's data.

    Args:
        account_data (dict): The account object.
        zone_domain (str): The domain name of the zone to find.

    Returns:
        dict or None: The zone object if found, otherwise None.
    """
    for zone in account_data.get("zones", []):
        if zone.get("domain") == zone_domain:
            return zone
    return None

def find_record(zone_data, record_name):
    """
    Finds a DNS record by its name within a zone's data.

    Args:
        zone_data (dict): The zone object.
        record_name (str): The name of the record to find.

    Returns:
        dict or None: The record object if found, otherwise None.
    """
    for record in zone_data.get("records", []):
        if record.get("name") == record_name:
            return record
    return None

def find_rotation_group(zone, group_name):
    """
    Finds a rotation group by its name within a zone's data.

    Args:
        zone (dict): The zone object.
        group_name (str): The name of the rotation group to find.

    Returns:
        dict or None: The rotation group object if found, otherwise None.
    """
    for group in zone.get("rotation_groups", []):
        if group.get("name") == group_name:
            return group
    return None

def load_rotation_status():
    """
    Loads the rotation status from the `rotation_status.json` file.

    This file tracks the last time a record or group was rotated to ensure
    rotations happen at the correct interval. If the file doesn't exist,
    it creates an empty one.

    Returns:
        dict: The rotation status data.
    """
    if not os.path.exists(ROTATION_STATUS_PATH):
        save_rotation_status({})
        return {}
    with open(ROTATION_STATUS_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from {ROTATION_STATUS_PATH}. Returning empty status.")
            return {}

def save_rotation_status(status_data):
    """
    Saves the rotation status data to the `rotation_status.json` file.

    Args:
        status_data (dict): The rotation status data to save.
    """
    with open(ROTATION_STATUS_PATH, "w") as f:
        json.dump(status_data, f, indent=2)

# Permissions required for different features. This structure is used to
# dynamically display guidance to the user and for validation.
REQUIRED_PERMISSIONS = {
    "features": {
        "IP Rotation Tool": ["Zone.DNS"],
        "Zone Management": ["Zone.DNS", "Zone.Zone", "Zone.Zone Settings"],
    },
    "permissions": {
        "Zone.Zone": "Edit",
        "Zone.DNS": "Edit",
        "Zone.Zone Settings": "Edit"
    },
    "validation_map": {
        "Zone:Edit": "Zone.Zone",
        "DNS:Edit": "Zone.DNS",
        "Zone_Settings:Edit": "Zone.Zone Settings"
    }
}
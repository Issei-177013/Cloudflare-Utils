import json
import os
from .validator import validate_config
from .logger import logger

# Determine the absolute path to the directory where this script (config_manager.py) is located.
# This ensures that configs.json and rotation_status.json are found relative to the script's location,
# which is crucial if the script is called from a different working directory (e.g., when installed as cfu).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "configs.json")
ROTATION_STATUS_PATH = os.path.join(SCRIPT_DIR, "rotation_status.json")

DEFAULT_ROTATION_INTERVAL_MINUTES = 30

def load_config():
    """Loads the configuration from the JSON file."""
    if not os.path.exists(CONFIG_PATH):
        logger.info(f"Config file not found at {CONFIG_PATH}. Creating a new one.")
        save_config({"accounts": []}) # Save default structure
        return {"accounts": []}
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Could not decode JSON from {CONFIG_PATH}. Returning default config.")
        # Optionally, handle this more gracefully, e.g., by backing up the broken file.
        return {"accounts": []} # Default structure on error

def validate_and_save_config(data):
    """Validates the configuration and saves it if valid."""
    try:
        validate_config(data)
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        return False

def save_config(data):
    """Saves the configuration data to the JSON file."""
    validate_and_save_config(data)

def find_account(data, account_name):
    """Finds an account by name in the config data."""
    for acc in data.get("accounts", []):
        if acc.get("name") == account_name:
            return acc
    return None

def find_zone(account_data, zone_domain):
    """Finds a zone by domain within an account's data."""
    for zone in account_data.get("zones", []):
        if zone.get("domain") == zone_domain:
            return zone
    return None

def find_record(zone_data, record_name):
    """Finds a record by name within a zone's data."""
    for record in zone_data.get("records", []):
        if record.get("name") == record_name:
            return record
    return None

def find_rotation_group(zone, group_name):
    """Finds a rotation group by name within a zone."""
    for group in zone.get("rotation_groups", []):
        if group.get("name") == group_name:
            return group
    return None

def load_rotation_status():
    if not os.path.exists(ROTATION_STATUS_PATH):
        save_rotation_status({})
        return {}
    with open(ROTATION_STATUS_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from {ROTATION_STATUS_PATH}. Returning empty status.")
            return {} # Return empty dict if file is corrupted or empty

def save_rotation_status(status_data):
    with open(ROTATION_STATUS_PATH, "w") as f:
        json.dump(status_data, f, indent=2)

# Permissions required for different features. This structure is used to
# dynamically display guidance to the user and for validation.
REQUIRED_PERMISSIONS = {
    "features": {
        "IP Rotation Tool": ["Zone.DNS"],
        "Zone Management": ["Zone.DNS", "Zone.Zone"],
    },
    "permissions": {
        "Zone.Zone": "Edit",
        "Zone.DNS": "Edit",
    },
    "validation_map": {
        "Zone:Read": "Zone.Zone",
        "DNS:Read": "Zone.DNS"
    }
}
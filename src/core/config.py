"""
Configuration Management.

This module provides a singleton `ConfigManager` class for handling the
application's configuration, which is stored in a JSON file. This approach
encapsulates all configuration-related logic, providing a single, consistent
interface for the rest of the application.
"""
import json
import os
from threading import Lock
from .validator import validate_config
from .logger import logger
from .exceptions import ConfigError

class ConfigManager:
    """
    Manages loading, saving, and accessing the application configuration.

    This class is implemented as a singleton to ensure that all parts of the
    application access the same configuration instance. It handles the
    underlying JSON file operations and provides a clean, mockable interface.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path=None):
        if not hasattr(self, '_initialized'):
            with self._lock:
                if not hasattr(self, '_initialized'):
                    self._initialized = True
                    self.config_path = config_path or self._get_default_config_path()
                    self.config_data = {}
                    self.load_config()

    def _get_default_config_path(self):
        """Determines the default path for the configs.json file."""
        # Project root is three levels up from src/core/config.py
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(project_root, "configs", "configs.json")

    def _get_default_config(self):
        """Returns the default configuration structure."""
        return {
            "accounts": [],
            "agents": [],
            "settings": {"console_logging": True},
            "bot": {
                "enabled": False,
                "token": "",
                "allowed_user_ids": [],
                "lang": "en"
            },
            "self_monitor": {
                "enabled": False,
                "name": "Master",
                "threshold_gb": 1000,
                "interval": 5,
                "targets": [],
                "alarms": [],
                "vnstat_interface": "eth0"
            }
        }

    def load_config(self, data=None):
        """
        Loads configuration from a file or an in-memory dictionary.

        If `data` is provided, it loads it into the config manager (for testing).
        Otherwise, it loads from the `configs.json` file.

        Args:
            data (dict, optional): A dictionary to load as the config.
        """
        if data is not None:
            self.config_data = data
            logger.info("Configuration loaded from in-memory dictionary.")
            return

        if not os.path.exists(self.config_path):
            logger.info(f"Config file not found at {self.config_path}. Creating a new one.")
            self.config_data = self._get_default_config()
            self.save_config()
        else:
            try:
                with open(self.config_path, "r") as f:
                    self.config_data = json.load(f)
                # Ensure default keys exist
                defaults = self._get_default_config()
                for key, value in defaults.items():
                    self.config_data.setdefault(key, value)
            except json.JSONDecodeError:
                logger.error(f"Could not decode JSON from {self.config_path}. Loading default config.")
                self.config_data = self._get_default_config()

    def get_config(self):
        """
        Returns the entire configuration data dictionary.

        Returns:
            dict: The configuration data.
        """
        return self.config_data

    def save_config(self):
        """
        Validates and saves the current configuration data to `configs.json`.

        Raises:
            ConfigError: If the configuration validation fails.
        """
        try:
            validate_config(self.config_data)
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.config_data, f, indent=2)
            logger.info(f"Configuration successfully saved to {self.config_path}")
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ConfigError(f"Configuration validation failed: {e}")

    def find_account(self, account_name):
        """Finds an account by its name."""
        for acc in self.config_data.get("accounts", []):
            if acc.get("name") == account_name:
                return acc
        return None

    def find_zone(self, account_data, zone_domain):
        """Finds a zone by its domain name within an account's data."""
        for zone in account_data.get("zones", []):
            if zone.get("domain") == zone_domain:
                return zone
        return None

    def find_record(self, zone_data, record_name):
        """Finds a DNS record by its name within a zone's data."""
        for record in zone_data.get("records", []):
            if record.get("name") == record_name:
                return record
        return None
    
    def find_rotation_group(self, zone, group_name):
        """Finds a rotation group by its name within a zone's data."""
        for group in zone.get("rotation_groups", []):
            if group.get("name") == group_name:
                return group
        return None

    def get_bot_lang(self):
        """Returns the bot's language from the configuration."""
        return self.config_data.get("bot", {}).get("lang", "en")

    def set_bot_lang(self, lang):
        """Sets the bot's language in the configuration."""
        self.config_data.setdefault("bot", {})["lang"] = lang
        self.save_config()

# --- Constants and other config-related utilities ---

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROTATION_STATUS_PATH = os.path.join(project_root, "configs", "rotation_status.json")
DEFAULT_ROTATION_INTERVAL_MINUTES = 30

def load_rotation_status():
    """Loads the rotation status from the `rotation_status.json` file."""
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
    """Saves the rotation status data to the `rotation_status.json` file."""
    os.makedirs(os.path.dirname(ROTATION_STATUS_PATH), exist_ok=True)
    with open(ROTATION_STATUS_PATH, "w") as f:
        json.dump(status_data, f, indent=2)

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

# Initialize the singleton instance for the application to use
config_manager = ConfigManager()
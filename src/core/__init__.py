"""
Core Package Initialization.

This file makes the 'core' directory a Python package and exposes key
components of the core logic to the rest of the application, simplifying
imports for the CLI and other modules.
"""

# Import key classes and modules to the package level
from . import accounts
from . import dns
from . import zones
from . import triggers
from . import dns_manager
from .config import config_manager
from .cloudflare_api import CloudflareAPI
from .logger import logger, configure_console_logging
from .exceptions import (
    CoreError,
    ConfigError,
    APIError,
    InvalidInputError,
    AuthenticationError
)

# You can also define an __all__ variable to specify what gets imported
# when a client does 'from src.core import *'
__all__ = [
    "accounts",
    "dns",
    "zones",
    "triggers",
    "dns_manager",
    "config_manager",
    "CloudflareAPI",
    "logger",
    "configure_console_logging",
    "CoreError",
    "ConfigError",
    "APIError",
    "InvalidInputError",
    "AuthenticationError"
]
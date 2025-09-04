"""
Core Utility Functions.

This module provides miscellaneous utility functions that are used across
the core application logic. These helpers encapsulate common, reusable
operations to maintain a clean and DRY codebase.
"""
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .config import config_manager

def format_datetime(dt):
    """
    Formats a datetime object into a string based on the configured timezone.

    It wraps the output in Left-to-Right Isolation (LRI) and Pop Directional
    Isolation (PDI) markers to ensure consistent display in mixed RTL/LTR
    environments, such as Telegram.

    Args:
        dt (datetime): The datetime object to format.

    Returns:
        str: The formatted datetime string (e.g., "<code>[LRI]YYYY-MM-DD HH:MM:SS ZONE[PDI]</code>").
    """
    try:
        # Default to UTC if not specified
        tz_name = config_manager.get_config().get("settings", {}).get("global", {}).get("timezone", "UTC")
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        # Fallback to UTC if the configured timezone is invalid
        tz_name = "UTC"
        tz = ZoneInfo(tz_name)

    # LRI and PDI markers for proper RTL/LTR handling in Telegram
    lri = "\u2068"
    pdi = "\u2069"
    
    # Format the datetime object
    formatted_dt = dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    
    return f"<code>{lri}{formatted_dt}{pdi}</code>"
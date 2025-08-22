import os
import sys
import time
from tabulate import tabulate
from .core.config import config_manager

# --- UI Configuration ---
def get_config_setting(key, default):
    """Helper to get a setting from the config file."""
    config = config_manager.get_config()
    return config.get("settings", {}).get(key, default)

def get_fast_mode_status():
    """
    Determines if FAST_MODE should be enabled. Defaults to False (slow mode on).
    """
    default_fast_mode = get_config_setting("fast_mode", False)
    env_var = os.environ.get("FAST_MODE")
    if env_var is not None:
        return env_var.lower() in ['true', '1', 't']
    return default_fast_mode

def get_slow_mode_delay():
    """Gets the slow mode delay from config, defaulting to 0.01."""
    return get_config_setting("slow_mode_delay", 0.01)

FAST_MODE = get_fast_mode_status()

# --- Color Constants ---
COLOR_SUCCESS = '\033[92m'
COLOR_ERROR = '\033[91m'
COLOR_WARNING = '\033[93m'
COLOR_INFO = '\033[94m'
COLOR_TITLE = '\033[96m'
COLOR_SEPARATOR = '\033[93m'
COLOR_CF_ORANGE = '\033[38;2;246;130;31m'
COLOR_CF_YELLOW = '\033[38;2;251;173;65m'
COLOR_CF_WHITE  = "\033[38;2;255;255;255m"
COLOR_CF_GRAY   = "\033[38;2;200;200;200m"
RESET_COLOR = '\033[0m'

# --- Separator Styles ---
HEADER_LINE = "──────────────────────────────────────────────────"
FOOTER_LINE = "──────────────────────────────────────────────────"
OPTION_SEPARATOR = "• • • • •"

# --- Display Functions ---
def print_fast(text, end='\n'):
    """Prints text instantly. Alias for print()."""
    print(text, end=end)

def print_slow(text, end='\n'):
    """
    Prints text with a gradual 'typewriter' effect.
    Skips the effect if FAST_MODE is enabled.
    """
    if get_fast_mode_status():
        print(text, end=end)
        return
        
    delay = get_slow_mode_delay()
    # Buffer to handle ANSI escape codes
    ansi_buffer = ""
    in_ansi = False
    
    for char in text:
        if char == '\033':
            in_ansi = True
        
        if in_ansi:
            ansi_buffer += char
            if char.isalpha() or char == '~': # Typically end of an ANSI sequence
                in_ansi = False
                print(ansi_buffer, end='')
                ansi_buffer = ""
        else:
            print(char, end='', flush=True)
            time.sleep(delay)
    
    # Print the newline character
    print(end=end)

def truncate_text(text, max_length=30):
    """Truncates text to a certain length, adding '...' if truncated."""
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text

def summarize_list(items, max_items=2):
    """
    Summarizes a list of strings for display.
    If the list has more than max_items, it shows the first and last items separated by '...'.
    """
    if not items:
        return ""
    if len(items) > max_items:
        return f"{items[0]}, ..., {items[-1]}"
    return ", ".join(items)

from .core.config import REQUIRED_PERMISSIONS

def display_as_table(data, headers):
    """
    Displays a list of dictionaries as a formatted table using the tabulate library.

    :param data: A list of dictionaries.
    :param headers: A list of keys to display as columns.
    """
    if not data:
        print_fast("No data to display.")
        return

    # The tabulate function can directly take a list of dictionaries and headers.
    print_fast(tabulate(data, headers=headers, tablefmt="grid"))

def display_token_guidance():
    """
    Displays guidance for creating a Cloudflare API token, including required permissions.
    """
    print_fast("\n🔐 How to create a valid Cloudflare API Token:")
    print_fast("Go to: https://dash.cloudflare.com/profile/api-tokens")
    print_fast('1. Click "Create Token"')
    print_fast('2. Select "Custom Token"')
    print_fast("3. Add the following permissions:")

    # Prepare data for the table
    permissions_list = []
    for perm, level in REQUIRED_PERMISSIONS['permissions'].items():
        permissions_list.append({
            'Permission': perm,
            'Access': level
        })

    # Display the table
    headers = {'Permission': 'Permission', 'Access': 'Access'}
    display_as_table(permissions_list, headers)

    print_fast("\n4. Apply to all zones")
    print_fast("5. Create and copy the token")
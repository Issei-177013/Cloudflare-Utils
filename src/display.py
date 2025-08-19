import os
import sys
import time
from tabulate import tabulate
from .config import load_config

# --- Configuration for Dynamic Display ---
def get_fast_mode_status():
    """
    Determines if FAST_MODE should be enabled.
    The setting from config.json is used, but can be overridden by an environment variable.
    Defaults to True (on).
    """
    config = load_config()
    # Get setting from config, default to True (on)
    fast_mode_in_config = config.get("settings", {}).get("fast_mode", True)
    
    # Environment variable FAST_MODE overrides the config file setting
    env_var = os.environ.get("FAST_MODE")
    if env_var is not None:
        return env_var.lower() in ['true', '1', 't']
        
    return fast_mode_in_config

FAST_MODE = get_fast_mode_status()
DEFAULT_DELAY = 0.03

# --- Separator Styles ---
HEADER_LINE = "──────────────────────────────────────────────────"
FOOTER_LINE = "──────────────────────────────────────────────────"
OPTION_SEPARATOR = "• • • • •"

# --- Dynamic Display Function ---
def print_slow(text, delay=DEFAULT_DELAY, end='\n'):
    """
    Prints text with a gradual 'typewriter' effect.
    Skips the effect if FAST_MODE is enabled.
    """
    if FAST_MODE:
        print(text, end=end)
        return

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

from .config import REQUIRED_PERMISSIONS

def display_as_table(data, headers):
    """
    Displays a list of dictionaries as a formatted table using the tabulate library.

    :param data: A list of dictionaries.
    :param headers: A list of keys to display as columns.
    """
    if not data:
        print_slow("No data to display.")
        return

    # The tabulate function can directly take a list of dictionaries and headers.
    print_slow(tabulate(data, headers=headers, tablefmt="grid"))

def display_token_guidance():
    """
    Displays guidance for creating a Cloudflare API token, including required permissions.
    """
    print_slow("\n🔐 How to create a valid Cloudflare API Token:")
    print_slow("Go to: https://dash.cloudflare.com/profile/api-tokens")
    print_slow('1. Click "Create Token"')
    print_slow('2. Select "Custom Token"')
    print_slow("3. Add the following permissions:")

    # Prepare data for the table
    permissions_list = []
    for perm, level in REQUIRED_PERMISSIONS['permissions'].items():
        permissions_list.append({
            'Permission': perm,
            'Access': level
        })

    # Display the table
    headers = ["Permission", "Access"]
    display_as_table(permissions_list, headers)

    print_slow("\n4. Apply to all zones")
    print_slow("5. Create and copy the token")
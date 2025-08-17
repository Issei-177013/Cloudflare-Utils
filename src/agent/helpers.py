import os
import json
import subprocess
import datetime
import psutil
import socket

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    """
    Loads the agent configuration from config.json, applying defaults for
    any missing values.
    """
    defaults = {
        "api_key": "default-key",
        "whitelist": ["127.0.0.1"],
        "vnstat_interface": "eth0",
        "port": 15728
    }

    if not os.path.exists(CONFIG_PATH):
        print(f"Warning: Configuration file not found at {CONFIG_PATH}. Using fallback defaults.")
        return defaults
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {CONFIG_PATH}. Using defaults.")
        return defaults

    # Ensure all default keys are present in the loaded config
    for key, value in defaults.items():
        config.setdefault(key, value)
    
    return config

def get_hostname():
    """Returns the server's hostname."""
    return socket.gethostname()

def get_uptime():
    """Returns the server uptime in a human-readable format."""
    try:
        boot_time_timestamp = psutil.boot_time()
        boot_time = datetime.datetime.fromtimestamp(boot_time_timestamp)
        now = datetime.datetime.now()
        delta = now - boot_time
        
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        return f"{days} days, {hours} hours, {minutes} minutes"
    except Exception:
        return "N/A"

def get_vnstat_data(interface, json_mode=None):
    """
    Fetches traffic data from vnstat for the specified interface.
    Accepts an optional json_mode to customize the query (e.g., 'h' for hourly).
    Returns parsed JSON data or an error message.
    """
    command = ['vnstat', '--json']
    if json_mode:
        command.append(json_mode)
    command.extend(['-i', interface])
        
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        # If vnstat returns no output, it means there's no data.
        # Return a valid, empty vnstat-like JSON structure to avoid parsing errors.
        if not result.stdout.strip():
            # This structure mimics a valid vnstat response with no traffic data,
            # allowing the calling function to handle it gracefully.
            return {"interfaces": [{"name": interface, "traffic": {}}]}, None

        data = json.loads(result.stdout)
        return data, None
    except FileNotFoundError:
        return None, "vnstat command not found. Is it installed and in the system's PATH?"
    except subprocess.CalledProcessError as e:
        error_message = f"vnstat error: {e.stderr.strip()}"
        if "not found" in e.stderr.lower():
            error_message = f"Interface '{interface}' not found by vnstat. Check your config."
        return None, error_message
    except json.JSONDecodeError:
        return None, "Failed to parse vnstat JSON output."
    except Exception as e:
        return None, f"An unexpected error occurred: {str(e)}"
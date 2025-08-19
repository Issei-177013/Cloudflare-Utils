import json
import subprocess
import datetime
import psutil
import socket

# --- Version Info ---
# In the agent, this is imported from a version file.
# For the self-monitor, we can hardcode it or leave it as N/A.
SELF_MONITOR_VERSION = "1.0.0 (self-monitor)"

# --- Helper Functions (copied from src/agent/helpers.py) ---

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
    
    # If no interface is specified, vnstat will use its default.
    # This might need to be configurable in the future.
    if interface:
        command.extend(['-i', interface])

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            error_message = result.stderr.strip() or "vnstat returned an error with no message"
            return None, f"vnstat error: {error_message}"

        stdout = result.stdout.strip()

        if not stdout:
            # This can happen if vnstat has no data for the interface.
            # Return a structure that looks like vnstat's output for an empty interface.
            return {"interfaces": [{"name": interface, "traffic": {}}]}, None

        try:
            data = json.loads(stdout)
            return data, None
        except json.JSONDecodeError as e:
            snippet = stdout[:300].replace("\n", " ")
            return None, f"Failed to parse vnstat JSON output: {str(e)} | Raw snippet: {snippet}"

    except FileNotFoundError:
        return None, "vnstat command not found. Is it installed and in the system's PATH?"
    except Exception as e:
        return None, f"An unexpected error occurred: {str(e)}"

# --- API-like Functions (to be called by the main app) ---

def get_status():
    """
    Returns the current status, mimicking the agent's /status endpoint.
    """
    return {
        "agent_version": SELF_MONITOR_VERSION,
        "hostname": get_hostname(),
        "uptime": get_uptime(),
        "status": "ok"
    }

def get_usage_by_period(interface, period):
    """
    Returns network usage for a specified period, mimicking the agent's
    /usage_by_period endpoint.
    """
    if not period:
        return {"error": "The 'period' parameter is required."}

    vnstat_data, error = get_vnstat_data(interface, json_mode=period)

    if error:
        return {"error": error}

    # vnstat sometimes returns data for a different interface if the requested one isn't found.
    # We need to find the specific interface data.
    interface_data = next((iface for iface in vnstat_data.get('interfaces', []) if iface.get('name') == interface), None)
    if not interface_data:
        # If the interface is not in the output, it's an error or there's no data.
        return {"error": f"Could not find data for interface '{interface}' in vnstat output."}
    
    traffic_data = interface_data.get('traffic', {})

    title_map = {
        'd': 'Daily', 'm': 'Monthly', 'y': 'Yearly',
        'h': 'Hourly', 't': 'Top Days', 'f': 'Five Minutes'
    }
    data_key_map = {
        'd': 'day', 'm': 'month', 'y': 'year',
        'h': 'hour', 't': 'top', 'f': 'fiveminute'
    }

    period_title = title_map.get(period, f"Unknown Period '{period}'")
    data_key = data_key_map.get(period)

    if not data_key or data_key not in traffic_data:
        return {
            "period_title": period_title,
            "data": []
        }

    return {
        "period_title": period_title,
        "data": traffic_data.get(data_key, [])
    }
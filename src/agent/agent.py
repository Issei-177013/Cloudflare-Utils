from flask import Flask, jsonify

# Import modularized components
from helpers import load_config, get_hostname, get_uptime, get_vnstat_data
from security import create_security_decorator

# --- Application Setup ---
try:
    from version import __version__
    AGENT_VERSION = f"Version: {__version__}"
except ImportError:
    AGENT_VERSION = "Version: N/A"
    
app = Flask(__name__)

# Load configuration and create the security decorator
config = load_config()
secure_route = create_security_decorator(config)


# --- API Endpoints ---

@app.route('/status', methods=['GET'])
@secure_route
def get_status_route():
    """Returns the current status of the agent and server."""
    status_info = {
        "agent_version": AGENT_VERSION,
        "hostname": get_hostname(),
        "uptime": get_uptime(),
        "status": "ok"
    }
    return jsonify(status_info)

@app.route('/usage', methods=['GET'])
@secure_route
def get_usage_route():
    """Returns network usage statistics from vnstat."""
    interface = config.get('vnstat_interface')
    vnstat_data, error = get_vnstat_data(interface)

    if error:
        return jsonify({"error": error}), 500

    # Find the specific interface data from vnstat output using a generator expression
    interface_data = next((iface for iface in vnstat_data.get('interfaces', []) if iface.get('name') == interface), None)

    if not interface_data:
        return jsonify({"error": f"Could not find data for interface '{interface}' in vnstat output."}), 500

    traffic = interface_data.get('traffic', {})
    today = traffic.get('day', [{}])[0]
    current_month = traffic.get('month', [{}])[0]
    
    # vnstat JSON output for daily/monthly is in KiB, convert to bytes
    bytes_in_kib = 1024

    usage_stats = {
        "interface": interface,
        "today": {
            "rx_bytes": today.get('rx', 0) * bytes_in_kib,
            "tx_bytes": today.get('tx', 0) * bytes_in_kib,
            "total_bytes": (today.get('rx', 0) + today.get('tx', 0)) * bytes_in_kib
        },
        "this_month": {
            "rx_bytes": current_month.get('rx', 0) * bytes_in_kib,
            "tx_bytes": current_month.get('tx', 0) * bytes_in_kib,
            "total_bytes": (current_month.get('rx', 0) + current_month.get('tx', 0)) * bytes_in_kib
        }
    }
    return jsonify(usage_stats)

@app.route('/action', methods=['POST'])
@secure_route
def handle_action_route():
    """Placeholder for triggering actions on the agent."""
    return jsonify({"status": "action endpoint not yet implemented"}), 501


# --- Main Execution ---

if __name__ == '__main__':
    # For production, a proper WSGI server like Gunicorn should be used.
    # This basic runner is for development and simplicity.
    app.run(host='0.0.0.0', port=config.get('port'))
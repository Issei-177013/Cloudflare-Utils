from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from collections import defaultdict

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
    
    usage_stats = {
        "interface": interface,
        "today": {
            "rx_bytes": today.get('rx', 0),
            "tx_bytes": today.get('tx', 0),
            "total_bytes": today.get('rx', 0) + today.get('tx', 0)
        },
        "this_month": {
            "rx_bytes": current_month.get('rx', 0),
            "tx_bytes": current_month.get('tx', 0),
            "total_bytes": current_month.get('rx', 0) + current_month.get('tx', 0)
        }
    }
    return jsonify(usage_stats)

@app.route('/action', methods=['POST'])
@secure_route
def handle_action_route():
    """Placeholder for triggering actions on the agent."""
    return jsonify({"status": "action endpoint not yet implemented"}), 501


@app.route('/usage_by_period', methods=['GET'])
@secure_route
def get_usage_by_period_route():
    """
    Returns network usage statistics for a specified period by passing the
    period directly to vnstat's json mode.
    """
    interface = config.get('vnstat_interface')
    # The 'period' parameter now directly corresponds to a vnstat json mode (d, m, y, h, t, f)
    period = request.args.get('period')

    if not period:
        return jsonify({"error": "The 'period' parameter is required."}), 400

    vnstat_data, error = get_vnstat_data(interface, json_mode=period)

    if error:
        return jsonify({"error": error}), 500

    interface_data = next((iface for iface in vnstat_data.get('interfaces', []) if iface.get('name') == interface), None)
    if not interface_data:
        return jsonify({"error": f"Could not find data for interface '{interface}' in vnstat output."}), 500
    
    traffic_data = interface_data.get('traffic', {})

    # Map vnstat mode to a human-readable title for the client
    title_map = {
        'd': 'Daily', 'm': 'Monthly', 'y': 'Yearly',
        'h': 'Hourly', 't': 'Top Days', 'f': 'Five Minutes'
    }
    # Map vnstat mode to the key in the traffic object where the data is stored
    data_key_map = {
        'd': 'day', 'm': 'month', 'y': 'year',
        'h': 'hour', 't': 'top', 'f': 'fiveminute'
    }

    period_title = title_map.get(period, f"Unknown Period '{period}'")
    data_key = data_key_map.get(period)

    # Check if the expected data key exists in the vnstat output
    if not data_key or data_key not in traffic_data:
        return jsonify({
            "period_title": period_title,
            "data": [] # Return an empty list if no data is available for that period
        })

    # Return the title and the list of traffic data for the requested period
    return jsonify({
        "period_title": period_title,
        "data": traffic_data.get(data_key, [])
    })


# --- Main Execution ---

if __name__ == '__main__':
    # For production, a proper WSGI server like Gunicorn should be used.
    # This basic runner is for development and simplicity.
    app.run(host='0.0.0.0', port=config.get('port'))
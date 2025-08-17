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
    Returns network usage statistics for a specified period.
    Supports 'hourly', 'weekly', '15-day', and 'custom' periods.
    """
    interface = config.get('vnstat_interface')
    period = request.args.get('period', 'daily') # Default to daily if not specified

    # Custom period has its own complex logic
    if period == 'custom':
        days = int(request.args.get('days', 0))
        hours = int(request.args.get('hours', 0))
        # vnstat doesn't support minute-level granularity, so we ignore it.

        total_hours = (days * 24) + hours
        
        # Fetch daily and hourly data. We need both to cover a larger custom range.
        daily_data, error_d = get_vnstat_data(interface, json_mode='d')
        hourly_data, error_h = get_vnstat_data(interface, json_mode='h')

        if error_d or error_h:
            return jsonify({"error": error_d or error_h}), 500

        interface_daily = next((iface for iface in daily_data.get('interfaces', []) if iface.get('name') == interface), None)
        interface_hourly = next((iface for iface in hourly_data.get('interfaces', []) if iface.get('name') == interface), None)

        if not interface_daily or not interface_hourly:
            return jsonify({"error": "Could not find interface data"}), 500

        # Combine data from days and hours to fulfill the request
        total_rx = 0
        total_tx = 0
        
        # Get full days data
        full_days_to_process = total_hours // 24
        days_traffic = interface_daily.get('traffic', {}).get('day', [])
        
        # Iterate over the most recent full days
        for day in days_traffic[-full_days_to_process:]:
            total_rx += day.get('rx', 0)
            total_tx += day.get('tx', 0)
            
        # Get remaining hours data
        remaining_hours = total_hours % 24
        hours_traffic = interface_hourly.get('traffic', {}).get('hour', [])
        
        # Iterate over the most recent remaining hours
        for hour in hours_traffic[-remaining_hours:]:
            total_rx += hour.get('rx', 0)
            total_tx += hour.get('tx', 0)

        custom_data = {
            "rx": total_rx,
            "tx": total_tx,
            "total": total_rx + total_tx,
            "query": {"days": days, "hours": hours}
        }
        return jsonify({"period": "custom", "data": custom_data})

    # Determine json_mode for other periods
    json_mode = 'h' if period == 'hourly' else 'd'
    
    vnstat_data, error = get_vnstat_data(interface, json_mode=json_mode)
    if error:
        return jsonify({"error": error}), 500

    interface_data = next((iface for iface in vnstat_data.get('interfaces', []) if iface.get('name') == interface), None)
    if not interface_data:
        return jsonify({"error": f"Could not find data for interface '{interface}' in vnstat output."}), 500
    
    traffic_data = interface_data.get('traffic', {})
    
    # Post-process for weekly and 15-day period
    if period == 'weekly':
        daily_traffic = traffic_data.get('day', [])
        weekly_traffic = defaultdict(lambda: {'rx': 0, 'tx': 0, 'date': {}})
        
        # Aggregate daily into weekly
        for day in daily_traffic:
            date_obj = datetime(day['date']['year'], day['date']['month'], day['date']['day'])
            start_of_week = date_obj - timedelta(days=date_obj.weekday())
            week_key = start_of_week.strftime('%Y-%m-%d')
            
            weekly_traffic[week_key]['rx'] += day.get('rx', 0)
            weekly_traffic[week_key]['tx'] += day.get('tx', 0)
            if not weekly_traffic[week_key]['date']:
                 weekly_traffic[week_key]['date'] = {'year': start_of_week.year, 'month': start_of_week.month, 'day': start_of_week.day}
        
        # The data structure for the client
        final_data = {'week': sorted(list(weekly_traffic.values()), key=lambda x: (x['date']['year'], x['date']['month'], x['date']['day']))}
        return jsonify({"period": "weekly", "data": final_data})

    elif period == '15-day':
        if 'day' in traffic_data:
            traffic_data['day'] = traffic_data['day'][-15:]
        # The period for the client is 'day' not '15-day'
        return jsonify({"period": "day", "data": traffic_data})

    # For 'hourly' and 'daily'
    return jsonify({"period": period, "data": traffic_data})


# --- Main Execution ---

if __name__ == '__main__':
    # For production, a proper WSGI server like Gunicorn should be used.
    # This basic runner is for development and simplicity.
    app.run(host='0.0.0.0', port=config.get('port'))
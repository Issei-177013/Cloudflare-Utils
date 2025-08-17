"""
Menu for Traffic Monitoring.

This module provides the user interface for managing monitoring agents,
viewing their status, and checking traffic usage.
"""
import requests

from ..config import load_config, save_config
from ..display import display_as_table
from ..input_helper import get_user_input, get_numeric_input
from ..logger import logger
from .utils import clear_screen, confirm_action

def list_agents():
    """Lists all configured agents and their status."""
    config = load_config()
    agents = config.get("agents", [])
    
    if not agents:
        print("No agents configured.")
        input("\nPress Enter to return to the menu...")
        return

    headers = ["#", "Name", "URL", "Threshold (GB)", "Status", "Version", "Hostname"]
    rows = []
    
    for i, agent in enumerate(agents):
        status = "Offline"
        version = "N/A"
        hostname = "N/A"
        try:
            response = requests.get(f"{agent['url']}/status", headers={"X-API-Key": agent["api_key"]}, timeout=3)
            if response.status_code == 200:
                data = response.json()
                status = f"Online ({data.get('status', 'ok')})"
                version = data.get('agent_version', 'N/A')
                hostname = data.get('hostname', 'N/A')
            else:
                status = f"Error ({response.status_code})"
        except requests.RequestException:
            pass # Keep status as Offline
        
        rows.append([
            i + 1,
            agent["name"],
            agent["url"],
            agent["threshold_gb"],
            status,
            version,
            hostname
        ])
        
    clear_screen()
    print("--- Configured Agents ---")
    display_as_table(rows, headers)
    input("\nPress Enter to return to the menu...")


def add_agent():
    """Adds a new agent to the configuration by prompting for connection details."""
    config = load_config()
    
    clear_screen()
    print("--- Add New Agent ---")
    
    name = get_user_input("Enter a name for this agent (e.g., 'Server A'):")
    host = get_user_input("Enter the agent's IP address or hostname:")
    port = get_numeric_input("Enter the agent's port [default: 15728]:", int, default=15728)
    
    # Construct the URL, assuming http. A more advanced version could ask for the scheme.
    url = f"http://{host}:{port}"
    
    print(f"Agent URL will be: {url}")

    api_key = get_user_input("Enter the agent's API Key:")
    threshold_gb = get_numeric_input("Enter the monthly traffic threshold in GB:", float)

    new_agent = {
        "name": name,
        "url": url,
        "api_key": api_key,
        "threshold_gb": threshold_gb
    }
    
    config["agents"].append(new_agent)
    save_config(config)
    logger.info(f"Added new agent: {name} at {url}")
    print(f"\n✅ Agent '{name}' added successfully.")
    input("Press Enter to continue...")

def remove_agent():
    """Removes an existing agent from the configuration."""
    config = load_config()
    agents = config.get("agents", [])

    if not agents:
        print("No agents to remove.")
        input("\nPress Enter to return...")
        return

    clear_screen()
    print("--- Remove Agent ---")
    headers = ["#", "Name", "URL"]
    rows = [[i + 1, agent["name"], agent["url"]] for i, agent in enumerate(agents)]
    display_as_table(rows, headers)
    
    choice = get_numeric_input("\nEnter the # of the agent to remove (or 0 to cancel):", int, min_val=0, max_val=len(agents))

    if choice == 0:
        print("Cancelled.")
        return

    agent_to_remove = agents[choice - 1]
    if confirm_action(f"Are you sure you want to remove agent '{agent_to_remove['name']}'?"):
        config["agents"].pop(choice - 1)
        save_config(config)
        logger.info(f"Removed agent: {agent_to_remove['name']}")
        print(f"✅ Agent '{agent_to_remove['name']}' removed.")
    else:
        print("Removal cancelled.")
        
    input("\nPress Enter to continue...")


def view_agent_usage():
    """Views detailed traffic usage for a specific agent, with selectable time periods."""
    config = load_config()
    agents = config.get("agents", [])

    if not agents:
        print("No agents configured.")
        input("\nPress Enter to return...")
        return

    clear_screen()
    print("--- Select Agent to View Usage ---")
    headers = ["#", "Name", "URL"]
    rows = [[i + 1, agent["name"], agent["url"]] for i, agent in enumerate(agents)]
    display_as_table(rows, headers)
    
    agent_choice = get_numeric_input("\nEnter the # of the agent to view (or 0 to cancel):", int, min_val=0, max_val=len(agents))
    if agent_choice == 0:
        return

    agent = agents[agent_choice - 1]

    while True:
        clear_screen()
        print(f"--- Usage for {agent['name']} ---")
        print("Select a time period:")
        print("1. Daily & Monthly (Default)")
        print("2. Hourly")
        print("3. Weekly")
        print("4. Last 15 Days")
        print("5. Custom Timeframe")
        print("0. Back to Agent Selection")
        print("--------------------------------")
        
        period_choice = input("👉 Enter your choice: ").strip()

        if period_choice == '0':
            break
        elif period_choice == '1':
            fetch_and_display_default_usage(agent)
        elif period_choice in ['2', '3', '4', '5']:
            period_map = {'2': 'hourly', '3': 'weekly', '4': '15-day', '5': 'custom'}
            period = period_map[period_choice]
            
            params = {'period': period}
            if period == 'custom':
                days = get_numeric_input("Enter days:", int, default=0)
                hours = get_numeric_input("Enter hours:", int, default=0)
                minutes = get_numeric_input("Enter minutes:", int, default=0)
                params.update({'days': days, 'hours': hours, 'minutes': minutes})

            fetch_and_display_periodic_usage(agent, params)
        else:
            print("❌ Invalid choice. Please select a valid option.")
        
        input("\nPress Enter to continue...")

def fetch_and_display_default_usage(agent):
    """Fetches and displays the default (today/month) usage view."""
    try:
        response = requests.get(f"{agent['url']}/usage", headers={"X-API-Key": agent['api_key']}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            def bytes_to_gb(b):
                return b / (1024**3)

            today_total_gb = bytes_to_gb(data['today']['total_bytes'])
            month_total_gb = bytes_to_gb(data['this_month']['total_bytes'])
            threshold_gb = agent['threshold_gb']
            usage_percent = (month_total_gb / threshold_gb) * 100 if threshold_gb > 0 else 0

            print(f"\nInterface: {data['interface']}")
            print("\n--- Today ---")
            print(f"  Received: {bytes_to_gb(data['today']['rx_bytes']):.2f} GB")
            print(f"  Sent:     {bytes_to_gb(data['today']['tx_bytes']):.2f} GB")
            print(f"  Total:    {today_total_gb:.2f} GB")
            print("\n--- This Month ---")
            print(f"  Received: {bytes_to_gb(data['this_month']['rx_bytes']):.2f} GB")
            print(f"  Sent:     {bytes_to_gb(data['this_month']['tx_bytes']):.2f} GB")
            print(f"  Total:    {month_total_gb:.2f} GB")
            print("\n--- Threshold ---")
            print(f"  Monthly Threshold: {threshold_gb} GB")
            print(f"  Current Usage:     {month_total_gb:.2f} GB ({usage_percent:.2f}%)")
        else:
            print(f"\n❌ Error fetching usage: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"\n❌ Could not connect to agent. Details: {e}")

def fetch_and_display_periodic_usage(agent, params):
    """Fetches and displays usage for a specified period from the new endpoint."""
    try:
        response = requests.get(f"{agent['url']}/usage_by_period", headers={"X-API-Key": agent['api_key']}, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            period = result.get('period')
            data = result.get('data', {})
            
            def bytes_to_gb(b):
                return b / (1024**3)

            print(f"\n--- Usage for: {period.replace('_', ' ').title()} ---")

            if not data:
                print("No data returned for this period.")
                return

            # Map the requested period to the actual key in the vnstat JSON response
            period_key_map = {
                'hourly': 'hour',
                'weekly': 'week',
                '15-day': 'day', # Agent returns 'day' for this
                'daily': 'day'
            }
            # Use the original period for 'custom' as it has a different structure
            data_key = period_key_map.get(period, period)

            if isinstance(data.get(data_key), list):
                headers = ["Date", "Received (GB)", "Sent (GB)", "Total (GB)"]
                rows = []
                for entry in data[data_key]:
                    total_gb = bytes_to_gb(entry.get('rx', 0) + entry.get('tx', 0))
                    # Date formatting can be improved here in a future update
                    date_str = f"{entry.get('date', {}).get('year', '')}-{entry.get('date', {}).get('month', '')}-{entry.get('date', {}).get('day', '')}"
                    if 'time' in entry:
                         date_str += f" {entry['time']['hour']}:{entry['time']['minute']}"
                    rows.append([
                        date_str,
                        f"{bytes_to_gb(entry.get('rx', 0)):.3f}",
                        f"{bytes_to_gb(entry.get('tx', 0)):.3f}",
                        f"{total_gb:.3f}"
                    ])
                display_as_table(rows, headers)
            elif period == 'custom':
                query = data.get('query', {})
                print(f"  Query: {query.get('days')} days, {query.get('hours')} hours")
                total_gb = bytes_to_gb(data.get('total', 0))
                print(f"  Received: {bytes_to_gb(data.get('rx', 0)):.3f} GB")
                print(f"  Sent:     {bytes_to_gb(data.get('tx', 0)):.3f} GB")
                print(f"  Total:    {total_gb:.3f} GB")
            else: # Handle other formats or a single entry
                total_gb = bytes_to_gb(data.get('rx', 0) + data.get('tx', 0))
                print(f"  Received: {bytes_to_gb(data.get('rx', 0)):.3f} GB")
                print(f"  Sent:     {bytes_to_gb(data.get('tx', 0)):.3f} GB")
                print(f"  Total:    {total_gb:.3f} GB")

        else:
            print(f"\n❌ Error fetching usage: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"\n❌ Could not connect to agent. Details: {e}")


def traffic_monitoring_menu():
    """Main menu for traffic monitoring."""
    while True:
        clear_screen()
        print("--- Traffic Monitoring Menu ---")
        print("1. List Agents & Status")
        print("2. Add New Agent")
        print("3. Remove Agent")
        print("4. View Agent Usage")
        print("0. Back to Main Menu")
        print("-----------------------------")

        choice = input("👉 Enter your choice: ").strip()

        if choice == '1':
            list_agents()
        elif choice == '2':
            add_agent()
        elif choice == '3':
            remove_agent()
        elif choice == '4':
            view_agent_usage()
        elif choice == '0':
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print("❌ Invalid choice. Please select a valid option.")
            input("\nPress Enter to continue...")
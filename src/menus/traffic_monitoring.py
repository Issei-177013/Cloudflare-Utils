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
        print("1. Five Minutes")
        print("2. Hourly")
        print("3. Daily")
        print("4. Monthly")
        print("5. Yearly")
        print("6. Top Days")
        print("0. Back to Agent Selection")
        print("--------------------------------")
        
        period_choice = input("👉 Enter your choice: ").strip()

        if period_choice == '0':
            break

        # Map choice to vnstat json mode
        period_map = {
            '3': 'd', # daily
            '4': 'm', # monthly
            '5': 'y', # yearly
            '2': 'h', # hourly
            '6': 't', # top
            '1': 'f'  # five minutes
        }
        
        if period_choice in period_map:
            period = period_map[period_choice]
            params = {'period': period}
            fetch_and_display_periodic_usage(agent, params)
        else:
            print("❌ Invalid choice. Please select a valid option.")
        
        input("\nPress Enter to continue...")

def fetch_and_display_periodic_usage(agent, params):
    """
    Fetches and displays usage for a specified period from the agent.
    It now handles various vnstat data formats directly.
    """
    try:
        response = requests.get(f"{agent['url']}/usage_by_period", headers={"X-API-Key": agent['api_key']}, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            title = result.get('period_title', 'Usage Data')
            data_list = result.get('data', [])

            def bytes_to_gb(b):
                # Ensure input is a number, default to 0 if not
                return (b / (1024**3)) if isinstance(b, (int, float)) else 0

            print(f"\n--- {title} ---")

            if not data_list:
                print("No data returned for this period.")
                return

            # Prepare table headers and rows
            headers = ["Date", "Time", "Received (GB)", "Sent (GB)", "Total (GB)"]
            rows = []

            for entry in data_list:
                rx_gb = bytes_to_gb(entry.get('rx', 0))
                tx_gb = bytes_to_gb(entry.get('tx', 0))
                total_gb = rx_gb + tx_gb
                
                # Format date string from date object
                date_info = entry.get('date', {})
                date_str = f"{date_info.get('year', 'YYYY')}-{date_info.get('month', 'MM'):02d}-{date_info.get('day', 'DD'):02d}"

                # Format time string if time object exists
                time_info = entry.get('time', {})
                time_str = ""
                if 'hour' in time_info:
                    time_str = f"{time_info.get('hour'):02d}:{time_info.get('minute'):02d}"

                rows.append([
                    date_str,
                    time_str,
                    f"{rx_gb:.3f}",
                    f"{tx_gb:.3f}",
                    f"{total_gb:.3f}"
                ])
            
            # If no entry had a time string, the column is not needed
            has_time_data = any(row[1] for row in rows)
            
            if not has_time_data:
                # Remove the "Time" header and the corresponding empty column from all rows
                headers.pop(1)
                for row in rows:
                    row.pop(1)

            display_as_table(rows, headers)

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
"""
Menu for Traffic Monitoring.

This module provides the user interface for managing monitoring agents,
viewing their status, and checking traffic usage.
"""
import requests
from urllib.parse import urlsplit, urlunsplit

from ..config import load_config, save_config
from ..display import (
    display_as_table, print_slow, print_fast,
    OPTION_SEPARATOR, COLOR_WARNING, RESET_COLOR,
    COLOR_ERROR, COLOR_SUCCESS, COLOR_TITLE, COLOR_SEPARATOR
)
from ..helpers import format_period_date
from ..input_helper import get_user_input, get_numeric_input
from ..logger import logger
from .utils import clear_screen, confirm_action

def _get_latest_usage_gb(agent, period):
    """
    Fetches the latest usage for an agent for a given period and returns it in GB.
    Returns None if usage can't be fetched.
    """
    try:
        response = requests.get(
            f"{agent['url']}/usage_by_period",
            headers={"X-API-Key": agent["api_key"]},
            params={'period': period},
            timeout=3
        )
        if response.status_code == 200:
            data = response.json().get('data', [])
            if data:
                latest_entry = data[-1]
                total_bytes = latest_entry.get('rx', 0) + latest_entry.get('tx', 0)
                return total_bytes / (1024**3)
    except requests.RequestException:
        return None
    return None

def list_agents():
    """
    Lists all configured agents, their status, and a summary of recent usage.
    This function is designed to be displayed as part of the main traffic monitoring menu.
    """
    config = load_config()
    agents = config.get("agents", [])
    
    if not agents:
        print_fast(f"{COLOR_WARNING}No agents configured.{RESET_COLOR}\n")
        return

    headers = ["#", "Name", "Status", "Day Usage (GB)", "Month Usage (GB)", "Threshold (GB)", "Version", "Hostname"]
    rows = []
    
    for i, agent in enumerate(agents):
        status = f"{COLOR_ERROR}Offline{RESET_COLOR}"
        version = "N/A"
        hostname = "N/A"
        day_usage_str = "N/A"
        month_usage_str = "N/A"

        is_online = False
        try:
            response = requests.get(f"{agent['url']}/status", headers={"X-API-Key": agent["api_key"]}, timeout=3)
            if response.status_code == 200:
                data = response.json()
                status = f"{COLOR_SUCCESS}Online{RESET_COLOR}"
                version = data.get('agent_version', 'N/A')
                hostname = data.get('hostname', 'N/A')
                is_online = True
            else:
                status = f"{COLOR_ERROR}Error ({response.status_code}){RESET_COLOR}"
        except requests.RequestException:
            pass # Keep status as Offline

        if is_online:
            # Fetch usage only if the agent is online
            day_usage_gb = _get_latest_usage_gb(agent, 'd')
            month_usage_gb = _get_latest_usage_gb(agent, 'm')

            if day_usage_gb is not None:
                day_usage_str = f"{day_usage_gb:.3f}"
            if month_usage_gb is not None:
                month_usage_str = f"{month_usage_gb:.3f}"

        rows.append([
            i + 1,
            agent["name"],
            status,
            day_usage_str,
            month_usage_str,
            agent["threshold_gb"],
            version,
            hostname
        ])
        
    print_fast(f"{COLOR_TITLE}--- Agents Overview ---{RESET_COLOR}")
    display_as_table(rows, headers)


def add_agent():
    """Adds a new agent to the configuration by prompting for connection details."""
    config = load_config()
    
    clear_screen()
    print_fast(f"{COLOR_TITLE}--- Add New Agent ---{RESET_COLOR}")
    
    name = get_user_input("Enter a name for this agent (e.g., 'Server A'):")
    host = get_user_input("Enter the agent's IP address or hostname:")
    port = get_numeric_input("Enter the agent's port [default: 15728]:", int, default=15728)
    
    # Construct the URL, assuming http. A more advanced version could ask for the scheme.
    url = f"http://{host}:{port}"
    
    print_fast(f"Agent URL will be: {url}")

    api_key = get_user_input("Enter the agent's API Key:")
    threshold_gb = get_numeric_input("Enter the monthly traffic threshold in GB:", float)

    new_agent = {
        "name": name,
        "url": url,
        "api_key": api_key,
        "threshold_gb": threshold_gb
    }
    
    if "agents" not in config:
        config["agents"] = []
    config["agents"].append(new_agent)
    save_config(config)
    logger.info(f"Added new agent: {name} at {url}")
    print_fast(f"\n{COLOR_SUCCESS}✅ Agent '{name}' added successfully.{RESET_COLOR}")
    input("Press Enter to continue...")

def remove_agent():
    """Removes an existing agent from the configuration."""
    config = load_config()
    agents = config.get("agents", [])

    if not agents:
        print_fast(f"{COLOR_WARNING}No agents to remove.{RESET_COLOR}")
        input("\nPress Enter to return...")
        return

    clear_screen()
    print_fast(f"{COLOR_TITLE}--- Remove Agent ---{RESET_COLOR}")
    headers = ["#", "Name", "URL"]
    rows = [[i + 1, agent["name"], agent["url"]] for i, agent in enumerate(agents)]
    display_as_table(rows, headers)
    
    choice = get_numeric_input("\nEnter the # of the agent to remove (or 0 to cancel):", int, min_val=0, max_val=len(agents))

    if choice == 0:
        print_fast("Cancelled.")
        return

    agent_to_remove = agents[choice - 1]
    if confirm_action(f"Are you sure you want to remove agent '{agent_to_remove['name']}'?"):
        config["agents"].pop(choice - 1)
        save_config(config)
        logger.info(f"Removed agent: {agent_to_remove['name']}")
        print_fast(f"{COLOR_SUCCESS}✅ Agent '{agent_to_remove['name']}' removed.{RESET_COLOR}")
    else:
        print_fast("Removal cancelled.")
        
    input("\nPress Enter to continue...")


def edit_agent():
    """Edits an existing agent's details."""
    config = load_config()
    agents = config.get("agents", [])

    if not agents:
        print_fast(f"{COLOR_WARNING}No agents to edit.{RESET_COLOR}")
        input("\nPress Enter to return...")
        return

    clear_screen()
    print_fast(f"{COLOR_TITLE}--- Edit Agent ---{RESET_COLOR}")
    headers = ["#", "Name", "URL"]
    rows = [[i + 1, agent["name"], agent["url"]] for i, agent in enumerate(agents)]
    display_as_table(rows, headers)
    
    choice = get_numeric_input("\nEnter the # of the agent to edit (or 0 to cancel):", int, min_val=0, max_val=len(agents))

    if choice == 0:
        print_fast("Cancelled.")
        return

    agent_index = choice - 1
    agent = agents[agent_index]
    
    # Deconstruct URL to get host and port
    split_url = urlsplit(agent.get("url", ""))
    current_host = split_url.hostname or ""
    current_port = split_url.port or 15728

    print_fast(f"\n--- Editing Agent: {agent.get('name', 'N/A')} ---")
    print_fast("Press Enter to keep the current value.")

    new_name = get_user_input(f"Enter new name [{agent.get('name', '')}]:", default=agent.get('name', ''))
    
    new_host = get_user_input(f"Enter new host (IP/domain) [{current_host}]:", default=current_host)
    new_port = get_numeric_input(f"Enter new port [{current_port}]:", int, default=current_port)
    
    new_api_key = get_user_input(f"Enter new API Key [{agent.get('api_key', '')}]:", default=agent.get('api_key', ''))
    new_threshold_gb = get_numeric_input(f"Enter new monthly threshold in GB [{agent.get('threshold_gb', 0)}]:", float, default=agent.get('threshold_gb', 0))

    # Reconstruct the URL, assuming http
    new_url = f"http://{new_host}:{new_port}"

    # Update agent details in the list
    config["agents"][agent_index] = {
        "name": new_name,
        "url": new_url,
        "api_key": new_api_key,
        "threshold_gb": new_threshold_gb
    }

    save_config(config)
    logger.info(f"Edited agent: {new_name}")
    print_fast(f"\n{COLOR_SUCCESS}✅ Agent '{new_name}' updated successfully.{RESET_COLOR}")
    input("\nPress Enter to continue...")


def view_agent_usage():
    """Views detailed traffic usage for a specific agent, with selectable time periods."""
    config = load_config()
    agents = config.get("agents", [])

    if not agents:
        print_fast(f"{COLOR_WARNING}No agents configured.{RESET_COLOR}")
        input("\nPress Enter to return...")
        return

    clear_screen()
    print_fast(f"{COLOR_TITLE}--- Select Agent to View Usage ---{RESET_COLOR}")
    headers = ["#", "Name", "URL"]
    rows = [[i + 1, agent["name"], agent["url"]] for i, agent in enumerate(agents)]
    display_as_table(rows, headers)
    
    agent_choice = get_numeric_input("\nEnter the # of the agent to view (or 0 to cancel):", int, min_val=0, max_val=len(agents))
    if agent_choice == 0:
        return

    agent = agents[agent_choice - 1]

    while True:
        clear_screen()
        print_fast(f"{COLOR_TITLE}--- Usage for {agent['name']} ---{RESET_COLOR}")
        print_fast("Select a time period:")
        print_slow("1. Five Minutes")
        print_slow("2. Hourly")
        print_slow("3. Daily")
        print_slow("4. Monthly")
        print_slow("5. Yearly")
        print_slow("6. Top Days")
        print_slow("0. Back to Agent Selection")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")
        
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
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
        
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

            print_fast(f"\n{COLOR_TITLE}--- {title} ---{RESET_COLOR}")

            if not data_list:
                print_fast(f"{COLOR_WARNING}No data returned for this period.{RESET_COLOR}")
                return

            # Prepare table headers and rows
            headers = ["Date/Time", "Received (GB)", "Sent (GB)", "Total (GB)"]
            rows = []

            for entry in data_list:
                rx_gb = bytes_to_gb(entry.get('rx', 0))
                tx_gb = bytes_to_gb(entry.get('tx', 0))
                total_gb = rx_gb + tx_gb
                
                # Format date and time using the new helper
                date_str = format_period_date(entry, params.get('period'))

                rows.append([
                    date_str,
                    f"{rx_gb:.3f}",
                    f"{tx_gb:.3f}",
                    f"{total_gb:.3f}"
                ])

            display_as_table(rows, headers)

        else:
            print_fast(f"\n{COLOR_ERROR}❌ Error fetching usage: {response.status_code} - {response.text}{RESET_COLOR}")
    except requests.RequestException as e:
        print_fast(f"\n{COLOR_ERROR}❌ Could not connect to agent. Details: {e}{RESET_COLOR}")


def traffic_monitoring_menu():
    """Main menu for traffic monitoring."""
    while True:
        clear_screen()
        print_fast(f"{COLOR_TITLE}--- Traffic Monitoring ---{RESET_COLOR}")
        
        # Display the agent overview table at the top of the menu
        list_agents()

        print_fast(f"\n{COLOR_TITLE}--- Menu ---{RESET_COLOR}")
        print_slow("1. Add New Agent")
        print_slow("2. Remove Agent")
        print_slow("3. Edit Agent")
        print_slow("4. View Agent Usage Details")
        print_slow("0. Back to Main Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = input("👉 Enter your choice: ").strip()

        if choice == '1':
            add_agent()
        elif choice == '2':
            remove_agent()
        elif choice == '3':
            edit_agent()
        elif choice == '4':
            view_agent_usage()
        elif choice == '0':
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
            input("\nPress Enter to continue...")
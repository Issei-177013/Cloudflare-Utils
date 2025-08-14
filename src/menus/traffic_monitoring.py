"""
Menu for Traffic Monitoring.

This module provides the user interface for managing monitoring agents,
viewing their status, and checking traffic usage.
"""
import requests
from ..logger import logger
from ..config import load_config, save_config
from .utils import clear_screen, confirm_action, print_table
from ..input_helper import get_user_input, get_numeric_input

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
    print_table(headers, rows)
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
    print_table(headers, rows)
    
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
    """Views detailed traffic usage for a specific agent."""
    config = load_config()
    agents = config.get("agents", [])

    if not agents:
        print("No agents configured.")
        input("\nPress Enter to return...")
        return

    clear_screen()
    print("--- View Agent Usage ---")
    headers = ["#", "Name", "URL"]
    rows = [[i + 1, agent["name"], agent["url"]] for i, agent in enumerate(agents)]
    print_table(headers, rows)
    
    choice = get_numeric_input("\nEnter the # of the agent to view (or 0 to cancel):", int, min_val=0, max_val=len(agents))

    if choice == 0:
        print("Cancelled.")
        return
        
    agent = agents[choice - 1]
    clear_screen()
    print(f"--- Usage for {agent['name']} ---")
    
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

            print(f"Interface: {data['interface']}")
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
        print(f"\n❌ Error: Could not connect to agent at {agent['url']}. Details: {e}")

    input("\nPress Enter to return to the menu...")


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
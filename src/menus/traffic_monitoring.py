"""
Menu for Traffic Monitoring.

This module provides the user interface for managing monitoring agents,
viewing their status, and checking traffic usage.
"""
import requests
import os
import json
from urllib.parse import urlsplit, urlunsplit

from ..config import load_config, save_config
from ..display import (
    display_as_table, print_slow, print_fast,
    OPTION_SEPARATOR, COLOR_WARNING, RESET_COLOR,
    COLOR_ERROR, COLOR_SUCCESS, COLOR_TITLE, COLOR_SEPARATOR
)
from ..helpers import format_period_date
from ..input_helper import get_user_input, get_numeric_input, get_validated_input
from ..logger import logger
from .utils import clear_screen, confirm_action
from .. import self_monitor

def get_all_agents():
    """
    Loads configured agents from configs.json and prepends the self-monitor if enabled.
    """
    config = load_config()
    agents = config.get("agents", [])
    
    self_monitor_config = config.get("self_monitor", {})
    if self_monitor_config.get("enabled"):
        self_monitor_agent = {
            "name": self_monitor_config.get("name", "Self-Monitor"),
            "type": "self",
            "triggers": self_monitor_config.get("triggers", []),
            "is_local": True  # Treat it as local to prevent removal/editing via old methods
        }
        return [self_monitor_agent] + list(agents)
        
    return list(agents)

def _get_latest_usage_gb(agent, period):
    """
    Fetches the latest usage for an agent for a given period and returns it in GB.
    Returns None if usage can't be fetched.
    """
    data = []
    if agent.get("type") == "self":
        config = load_config()
        interface = config.get("self_monitor", {}).get("vnstat_interface")
        result = self_monitor.get_usage_by_period(interface, period)
        if "error" not in result:
            data = result.get('data', [])
    else:
        try:
            response = requests.get(
                f"{agent['url']}/usage_by_period",
                headers={"X-API-Key": agent["api_key"]},
                params={'period': period},
                timeout=3
            )
            if response.status_code == 200:
                data = response.json().get('data', [])
        except requests.RequestException:
            return None

    if data:
        latest_entry = data[-1]
        total_bytes = latest_entry.get('rx', 0) + latest_entry.get('tx', 0)
        return total_bytes / (1024**3)

    return None

def list_agents(agents):
    """
    Lists all configured agents, their status, and a summary of recent usage.
    """
    if not agents:
        print_fast(f"{COLOR_WARNING}No agents configured.{RESET_COLOR}\n")
        return

    headers = ["#", "Name", "Status", "Day Usage (GB)", "Month Usage (GB)", "Triggers", "Version", "Hostname"]
    rows = []
    
    for i, agent in enumerate(agents):
        status = f"{COLOR_ERROR}Offline{RESET_COLOR}"
        version = "N/A"
        hostname = "N/A"
        day_usage_str = "N/A"
        month_usage_str = "N/A"

        is_online = False
        if agent.get("type") == "self":
            data = self_monitor.get_status()
            if data.get("status") == "ok":
                status = f"{COLOR_SUCCESS}Online{RESET_COLOR}"
                version = data.get('agent_version', 'N/A')
                hostname = data.get('hostname', 'N/A')
                is_online = True
            else:
                status = f"{COLOR_ERROR}Error{RESET_COLOR}"
        else:
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
            day_usage_gb = _get_latest_usage_gb(agent, 'd')
            month_usage_gb = _get_latest_usage_gb(agent, 'm')

            if day_usage_gb is not None:
                day_usage_str = f"{day_usage_gb:.3f}"
            if month_usage_gb is not None:
                month_usage_str = f"{month_usage_gb:.3f}"

        trigger_count = len(agent.get("triggers", []))
        trigger_str = f"{trigger_count} triggers" if trigger_count > 0 else "None"

        rows.append([
            i + 1,
            agent["name"],
            status,
            day_usage_str,
            month_usage_str,
            trigger_str,
            version,
            hostname
        ])
        
    print_fast(f"\n{COLOR_TITLE}--- Agents Overview ---{RESET_COLOR}")
    display_as_table(rows, headers)

def add_agent():
    """Adds a new remote agent to the configuration."""
    config = load_config()
    
    clear_screen()
    print_fast(f"{COLOR_TITLE}--- Add New Agent ---{RESET_COLOR}")
    
    name = get_user_input("Enter a name for this agent (e.g., 'Server A'):")
    host = get_user_input("Enter the agent's IP address or hostname:")
    port = get_numeric_input("Enter the agent's port [default: 15728]:", int, default=15728)
    
    url = f"http://{host}:{port}"
    print_fast(f"Agent URL will be: {url}")

    api_key = get_user_input("Enter the agent's API Key:")

    new_agent = {
        "name": name,
        "url": url,
        "api_key": api_key,
        "triggers": []
    }
    
    if "agents" not in config:
        config["agents"] = []
    config["agents"].append(new_agent)
    # Move save_config to after the trigger menu
    logger.info(f"Added new agent: {name} at {url}")
    print_fast(f"\n{COLOR_SUCCESS}✅ Agent '{name}' added successfully.{RESET_COLOR}")

    if confirm_action("Do you want to add a trigger for this agent now?"):
        manage_agent_triggers_menu(new_agent, config)
    
    save_config(config)
    logger.info(f"Configuration saved for agent {name}.")
    input("\nPress Enter to continue...")

def remove_agent(agents):
    """Removes an existing agent from the configuration."""
    config = load_config()
    
    removable_agents = [agent for agent in agents if not agent.get("is_local")]
    if not removable_agents:
        print_fast(f"{COLOR_WARNING}No configurable agents to remove.{RESET_COLOR}")
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

    if agent_to_remove.get("is_local"):
        print_fast(f"\n{COLOR_WARNING}The Master (Local) agent cannot be removed.{RESET_COLOR}")
        input("Press Enter to continue...")
        return

    if confirm_action(f"Are you sure you want to remove agent '{agent_to_remove['name']}'?"):
        config_agents = config.get("agents", [])
        
        updated_config_agents = [
            agent for agent in config_agents 
            if not (agent.get('name') == agent_to_remove.get('name') and agent.get('url') == agent_to_remove.get('url'))
        ]
        
        if len(updated_config_agents) < len(config_agents):
            config["agents"] = updated_config_agents
            save_config(config)
            logger.info(f"Removed agent: {agent_to_remove['name']}")
            print_fast(f"{COLOR_SUCCESS}✅ Agent '{agent_to_remove['name']}' removed.{RESET_COLOR}")
        else:
            logger.error(f"Agent '{agent_to_remove['name']}' not found in config for removal.")
            print_fast(f"{COLOR_ERROR}An unexpected error occurred. Agent not found in config.{RESET_COLOR}")
    else:
        print_fast("Removal cancelled.")
        
    input("\nPress Enter to continue...")

def edit_single_agent(agent_to_edit):
    """Edits the details of a single agent."""
    config = load_config()

    config_agents = config.get("agents", [])
    agent_index_in_config = -1
    for i, agent in enumerate(config_agents):
        if agent.get('name') == agent_to_edit.get('name') and agent.get('url') == agent_to_edit.get('url'):
            agent_index_in_config = i
            break

    if agent_index_in_config == -1:
        logger.error(f"Agent '{agent_to_edit['name']}' not found in config for editing.")
        print_fast(f"{COLOR_ERROR}An unexpected error occurred. Agent not found in config.{RESET_COLOR}")
        input("\nPress Enter to continue...")
        return

    agent = config_agents[agent_index_in_config]
    
    split_url = urlsplit(agent.get("url", ""))
    current_host = split_url.hostname or ""
    current_port = split_url.port or 15728

    print_fast(f"\n--- Editing Agent: {agent.get('name', 'N/A')} ---")
    print_fast("Press Enter to keep the current value.")

    new_name = get_user_input(f"Enter new name [{agent.get('name', '')}]:", default=agent.get('name', ''))
    new_host = get_user_input(f"Enter new host (IP/domain) [{current_host}]:", default=current_host)
    new_port = get_numeric_input(f"Enter new port [{current_port}]:", int, default=current_port)
    new_api_key = get_user_input(f"Enter new API Key [{agent.get('api_key', '')}]:", default=agent.get('api_key', ''))

    new_url = f"http://{new_host}:{new_port}"

    # Preserve existing triggers
    existing_triggers = agent.get("triggers", [])

    config["agents"][agent_index_in_config] = {
        "name": new_name,
        "url": new_url,
        "api_key": new_api_key,
        "triggers": existing_triggers
    }

    save_config(config)
    logger.info(f"Edited agent: {new_name}")
    print_fast(f"\n{COLOR_SUCCESS}✅ Agent '{new_name}' core details updated successfully.{RESET_COLOR}")

    # After saving core details, offer to manage triggers
    if confirm_action("Do you want to manage triggers for this agent now?"):
        # We need to pass the updated agent object to the menu
        updated_agent = config["agents"][agent_index_in_config]
        manage_agent_triggers_menu(updated_agent)
    else:
        input("\nPress Enter to continue...")

def view_agent_usage(agents):
    """Views detailed traffic usage for a specific agent."""
    if not agents:
        print_fast(f"{COLOR_WARNING}No agents configured.{RESET_COLOR}")
        input("\nPress Enter to return...")
        return

    clear_screen()
    print_fast(f"{COLOR_TITLE}--- Select Agent to View Usage ---{RESET_COLOR}")
    
    headers = ["#", "Name", "Endpoint/Interface"]
    rows = []
    config = None 

    for i, agent in enumerate(agents):
        endpoint = ""
        if agent.get("type") == "self":
            if not config:
                config = load_config()
            endpoint = config.get("self_monitor", {}).get("vnstat_interface", "N/A")
        else:
            endpoint = agent.get("url", "N/A")
        
        rows.append([i + 1, agent["name"], endpoint])

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

        period_map = {
            '3': 'd', '4': 'm', '5': 'y', '2': 'h', '6': 't', '1': 'f'
        }
        
        if period_choice in period_map:
            params = {'period': period_map[period_choice]}
            fetch_and_display_periodic_usage(agent, params)
        else:
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
        
        input("\nPress Enter to continue...")

def fetch_and_display_periodic_usage(agent, params):
    """
    Fetches and displays usage for a specified period from the agent.
    """
    result = None
    if agent.get("type") == "self":
        config = load_config()
        interface = config.get("self_monitor", {}).get("vnstat_interface")
        result = self_monitor.get_usage_by_period(interface, params.get("period"))
    else:
        try:
            response = requests.get(f"{agent['url']}/usage_by_period", headers={"X-API-Key": agent['api_key']}, params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
            else:
                print_fast(f"\n{COLOR_ERROR}❌ Error fetching usage: {response.status_code} - {response.text}{RESET_COLOR}")
                return
        except requests.RequestException as e:
            print_fast(f"\n{COLOR_ERROR}❌ Could not connect to agent. Details: {e}{RESET_COLOR}")
            return

    if result:
        if "error" in result:
            print_fast(f"\n{COLOR_ERROR}❌ Error fetching usage: {result['error']}{RESET_COLOR}")
            return

        title = result.get('period_title', 'Usage Data')
        data_list = result.get('data', [])

        def bytes_to_gb(b):
            return (b / (1024**3)) if isinstance(b, (int, float)) else 0

        print_fast(f"\n{COLOR_TITLE}--- {title} ---{RESET_COLOR}")

        if not data_list:
            print_fast(f"{COLOR_WARNING}No data returned for this period.{RESET_COLOR}")
            return

        headers = ["Date/Time", "Received (GB)", "Sent (GB)", "Total (GB)"]
        rows = []

        for entry in data_list:
            rx_gb = bytes_to_gb(entry.get('rx', 0))
            tx_gb = bytes_to_gb(entry.get('tx', 0))
            total_gb = rx_gb + tx_gb
            date_str = format_period_date(entry, params.get('period'))

            rows.append([
                date_str,
                f"{rx_gb:.3f}",
                f"{tx_gb:.3f}",
                f"{total_gb:.3f}"
            ])

        display_as_table(rows, headers)

def edit_self_monitor_config():
    """Edits the Self-Monitor's configuration."""
    config = load_config()
    self_monitor_config = config.get("self_monitor", {})

    # It's better to allow editing even when disabled.
    # if not self_monitor_config.get("enabled"):
    #     print_fast(f"\n{COLOR_WARNING}The Self-Monitor is not enabled. Please enable it first to edit its configuration.{RESET_COLOR}")
    #     input("Press Enter to continue...")
    #     return

    clear_screen()
    print_fast(f"{COLOR_TITLE}--- Edit Self-Monitor Configuration ---{RESET_COLOR}")
    print_fast("Press Enter to keep the current value.")

    current_name = self_monitor_config.get('name', 'Self-Monitor')
    current_interface = self_monitor_config.get('vnstat_interface', 'eth0')

    new_name = get_user_input(f"Enter new name [{current_name}]:", default=current_name)
    new_interface = get_user_input(f"Enter new vnstat interface [{current_interface}]:", default=current_interface)

    config["self_monitor"]["name"] = new_name
    config["self_monitor"]["vnstat_interface"] = new_interface

    save_config(config)
    logger.info(f"Edited Self-Monitor configuration.")
    print_fast(f"\n{COLOR_SUCCESS}✅ Self-Monitor configuration updated successfully.{RESET_COLOR}")

    if confirm_action("Do you want to manage triggers for the Self-Monitor now?"):
        # We need to get the updated self-monitor agent object to pass to the menu
        all_agents = get_all_agents()
        self_monitor_agent = next((agent for agent in all_agents if agent.get("type") == "self"), None)
        if self_monitor_agent:
            manage_agent_triggers_menu(self_monitor_agent)
    else:
        input("\nPress Enter to continue...")

def edit_monitor_menu():
    """Menu for selecting a monitor to edit."""
    all_agents = get_all_agents()

    if not all_agents:
        print_fast(f"{COLOR_WARNING}No monitors configured or enabled to edit.{RESET_COLOR}")
        input("\nPress Enter to return...")
        return

    clear_screen()
    print_fast(f"{COLOR_TITLE}--- Edit Monitor ---{RESET_COLOR}")
    
    headers = ["#", "Name", "Type", "URL/Interface"]
    rows = []
    for i, agent in enumerate(all_agents):
        if agent.get("type") == "self":
            config = load_config()
            interface = config.get("self_monitor", {}).get("vnstat_interface", "N/A")
            rows.append([i + 1, agent["name"], "Self-Monitor", interface])
        else:
            rows.append([i + 1, agent["name"], "Remote Agent", agent.get("url", "N/A")])

    display_as_table(rows, headers)
    
    choice = get_numeric_input("\nEnter the # of the monitor to edit (or 0 to cancel):", int, min_val=0, max_val=len(all_agents))

    if choice == 0:
        print_fast("Cancelled.")
        input("\nPress Enter to continue...")
        return

    agent_to_edit = all_agents[choice - 1]

    if agent_to_edit.get("type") == "self":
        edit_self_monitor_config()
    else:
        # The edit_single_agent function needs to be called within the context of the menu
        # It performs its own screen clearing and input prompts.
        edit_single_agent(agent_to_edit)

def toggle_self_monitor():
    """Toggles the self-monitor on or off."""
    config = load_config()
    self_monitor_config = config.get("self_monitor", {})
    is_enabled = self_monitor_config.get("enabled", False)

    if is_enabled:
        if confirm_action("The Self-Monitor is currently enabled. Do you want to disable it?"):
            config["self_monitor"]["enabled"] = False
            save_config(config)
            logger.info("Self-Monitor disabled.")
            print_fast(f"\n{COLOR_SUCCESS}✅ Self-Monitor has been disabled.{RESET_COLOR}")
        else:
            print_fast("Operation cancelled.")
    else:
        if confirm_action("The Self-Monitor is currently disabled. Do you want to enable it?"):
            current_interface = self_monitor_config.get('vnstat_interface', 'eth0')
            new_interface = get_user_input(f"Enter vnstat interface to monitor [{current_interface}]:", default=current_interface)
            
            # Ensure the self_monitor section exists
            if "self_monitor" not in config:
                config["self_monitor"] = {}

            config["self_monitor"]["vnstat_interface"] = new_interface
            config["self_monitor"]["enabled"] = True
            save_config(config)
            logger.info(f"Self-Monitor enabled on interface {new_interface}.")
            print_fast(f"\n{COLOR_SUCCESS}✅ Self-Monitor has been enabled on interface '{new_interface}'.{RESET_COLOR}")
        else:
            print_fast("Operation cancelled.")
    
    input("\nPress Enter to continue...")

def manage_agent_triggers_menu(agent, config):
    """
    Displays a menu to manage triggers for a specific agent.
    The config object is passed in to avoid multiple loads/saves.
    """
    while True:
        clear_screen()
        print_fast(f"{COLOR_TITLE}--- Manage Triggers for {agent['name']} ---{RESET_COLOR}")

        triggers = agent.get("triggers", [])
        if not triggers:
            print_fast(f"{COLOR_WARNING}No triggers configured for this agent.{RESET_COLOR}")
        else:
            headers = ["#", "Name", "Period", "Volume", "Type", "Action"]
            rows = []
            for i, trigger in enumerate(triggers):
                rows.append([
                    i + 1,
                    trigger.get('name'),
                    trigger.get('period'),
                    f"{trigger.get('volume_gb')} GB",
                    trigger.get('volume_type'),
                    trigger.get('action')
                ])
            display_as_table(rows, headers)

        print_fast(f"\n{COLOR_TITLE}--- Trigger Menu ---{RESET_COLOR}")
        print_slow("1. Add New Trigger")
        print_slow("2. Edit Trigger")
        print_slow("3. Remove Trigger")
        print_slow("0. Back to Main Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = input("👉 Enter your choice: ").strip()

        if choice == '1':
            add_trigger(agent, config)
        elif choice == '0':
            break
        else:
            print_fast(f"{COLOR_ERROR}❌ Invalid choice or not yet implemented.{RESET_COLOR}")
            input("\nPress Enter to continue...")


def add_trigger(agent, config):
    """
    Adds a new trigger to an agent's configuration.
    Does not save the config; expects the caller to handle it.
    """
    print_fast(f"\n{COLOR_TITLE}--- Add New Trigger ---{RESET_COLOR}")
    
    name = get_user_input("Enter a name for this trigger (e.g., 'Daily Download Limit'):")
    
    # --- Period Selection ---
    print_fast("Select the trigger period:")
    period_options = {'1': 'd', '2': 'w', '3': 'm'}
    print_slow("1. Daily (d)")
    print_slow("2. Weekly (w)")
    print_slow("3. Monthly (m)")
    period_choice = get_validated_input(
        "Enter choice: ",
        lambda x: x in period_options,
        "Invalid choice. Please select a valid option."
    )
    period = period_options[period_choice]

    # --- Volume GB ---
    volume_gb = get_numeric_input("Enter the traffic volume in GB:", float)

    # --- Volume Type ---
    print_fast("Select the volume type to monitor:")
    type_options = {'1': 'rx', '2': 'tx', '3': 'total'}
    print_slow("1. RX (Download)")
    print_slow("2. TX (Upload)")
    print_slow("3. Total (RX + TX)")
    type_choice = get_validated_input(
        "Enter choice: ",
        lambda x: x in type_options,
        "Invalid choice. Please select a valid option."
    )
    volume_type = type_options[type_choice]

    # --- Action ---
    print_fast("Select the action to perform:")
    action_options = {'1': 'alarm', '2': 'ip_rotate'}
    print_slow("1. Send Alarm")
    print_slow("2. Rotate IP")
    action_choice = get_validated_input(
        "Enter choice: ",
        lambda x: x in action_options,
        "Invalid choice. Please select a valid option."
    )
    action = action_options[action_choice]

    new_trigger = {
        "name": name,
        "period": period,
        "volume_gb": volume_gb,
        "volume_type": volume_type,
        "action": action
    }

    # The agent object is modified directly, which will be reflected in the config
    # object that was passed by reference.
    if "triggers" not in agent:
        agent["triggers"] = []
    agent["triggers"].append(new_trigger)
            
    logger.info(f"Staged new trigger '{name}' for agent '{agent['name']}'")
    print_fast(f"\n{COLOR_SUCCESS}✅ Trigger '{name}' added. It will be saved with the configuration.{RESET_COLOR}")
    input("Press Enter to continue...")


def traffic_monitoring_menu():
    """Main menu for traffic monitoring."""
    while True:
        clear_screen()
        
        all_agents = get_all_agents()
        config = load_config()
        self_monitor_enabled = config.get("self_monitor", {}).get("enabled", False)

        print_fast(f"{COLOR_TITLE}--- Traffic Monitoring ---{RESET_COLOR}")
        list_agents(all_agents)

        print_fast(f"\n{COLOR_TITLE}--- Menu ---{RESET_COLOR}")
        
        if self_monitor_enabled:
            print_slow("1. Disable Self-Monitor")
        else:
            print_slow("1. Enable Self-Monitor")

        print_slow("2. Add New Agent")
        print_slow("3. Remove Agent")
        print_slow("4. Edit Monitor")
        print_slow("5. View Monitor Usage Details")
        print_slow("0. Back to Main Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = input("👉 Enter your choice: ").strip()

        if choice == '1':
            toggle_self_monitor()
        elif choice == '2':
            add_agent()
        elif choice == '3':
            remove_agent(all_agents)
        elif choice == '4':
            edit_monitor_menu()
        elif choice == '5':
            view_agent_usage(all_agents)
        elif choice == '0':
            break
        else:
            logger.warning(f"Invalid choice: {choice}")
            print_fast(f"{COLOR_ERROR}❌ Invalid choice. Please select a valid option.{RESET_COLOR}")
            input("\nPress Enter to continue...")
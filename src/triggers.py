"""
Generic Trigger Management Module.

This module provides functions for creating, managing, and selecting
traffic-based triggers. These triggers can be used by various parts of the
application (e.g., IP rotation, consumption alarms) to initiate actions
based on an agent's traffic usage.
"""
import uuid
from .config import load_config, save_config
from .display import display_as_table, print_fast, print_slow, COLOR_TITLE, COLOR_SEPARATOR, OPTION_SEPARATOR, RESET_COLOR, COLOR_WARNING, COLOR_ERROR, COLOR_SUCCESS
from .input_helper import get_user_input, get_numeric_input, get_validated_input
from .logger import logger
from .menus.utils import clear_screen, select_from_list

def load_triggers():
    """Loads the triggers from the main configuration file."""
    config = load_config()
    return config.get("triggers", [])

def save_triggers(triggers):
    """Saves the triggers to the main configuration file."""
    config = load_config()
    config["triggers"] = triggers
    save_config(config)

def add_trigger(config):
    """
    Guides the user through creating a new trigger.
    Modifies the config object in place and returns the new trigger.
    """
    print_fast(f"\n{COLOR_TITLE}--- Create New Trigger ---{RESET_COLOR}")

    # --- Select Agent ---
    agents = config.get("agents", [])
    
    self_monitor_config = config.get("self_monitor", {})
    if self_monitor_config.get("enabled"):
        self_monitor_agent = {
            "name": self_monitor_config.get("name", "Self-Monitor"),
            "type": "self"
        }
        agents = [self_monitor_agent] + agents

    if not agents:
        print_fast(f"{COLOR_ERROR}No agents configured or self-monitor enabled. Please add an agent first.{RESET_COLOR}")
        return None
    
    print_fast("Select the agent this trigger will monitor:")
    agent_to_monitor = select_from_list(agents, "Select an agent:")
    if not agent_to_monitor:
        return None

    # --- Trigger Details ---
    name = get_user_input("Enter a name for this trigger (e.g., 'High Download on Server A'):")
    
    print_fast("Select the trigger period:")
    period_options = {'1': 'd', '2': 'w', '3': 'm'}
    print_slow("1. Daily (d)")
    print_slow("2. Weekly (w)")
    print_slow("3. Monthly (m)")
    period_choice = get_validated_input("Enter choice: ", lambda x: x in period_options, "Invalid choice.")
    period = period_options[period_choice]

    volume_gb = get_numeric_input("Enter the traffic volume threshold in GB:", float)

    print_fast("Select the volume type to monitor:")
    type_options = {'1': 'rx', '2': 'tx', '3': 'total'}
    print_slow("1. RX (Download)")
    print_slow("2. TX (Upload)")
    print_slow("3. Total (RX + TX)")
    type_choice = get_validated_input("Enter choice: ", lambda x: x in type_options, "Invalid choice.")
    volume_type = type_options[type_choice]

    new_trigger = {
        "id": f"trigger_{uuid.uuid4().hex[:8]}",
        "name": name,
        "agent_name": agent_to_monitor["name"],
        "period": period,
        "volume_gb": volume_gb,
        "volume_type": volume_type
    }

    if "triggers" not in config:
        config["triggers"] = []
    config["triggers"].append(new_trigger)
    
    logger.info(f"Staged new trigger '{name}' ({new_trigger['id']})")
    print_fast(f"\n{COLOR_SUCCESS}✅ Trigger '{name}' created successfully.{RESET_COLOR}")
    
    return new_trigger

def select_trigger():
    """
    Displays a UI for selecting an existing trigger or creating a new one.
    Returns the ID of the selected or newly created trigger.
    """
    config = load_config()
    
    while True:
        clear_screen()
        print_fast(f"{COLOR_TITLE}--- Select a Trigger ---{RESET_COLOR}")
        
        triggers = config.get("triggers", [])
        
        if not triggers:
            print_fast(f"{COLOR_WARNING}No triggers found.{RESET_COLOR}")
        else:
            headers = ["#", "Name", "Agent", "Period", "Volume", "Type"]
            rows = []
            for i, trigger in enumerate(triggers):
                rows.append([
                    i + 1,
                    trigger.get('name'),
                    trigger.get('agent_name'),
                    trigger.get('period'),
                    f"{trigger.get('volume_gb')} GB",
                    trigger.get('volume_type')
                ])
            display_as_table(rows, headers)

        print_fast("\n1. Select an existing trigger")
        print_fast("2. Create a new trigger")
        print_fast("0. Cancel")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = get_user_input("Enter your choice: ")

        if choice == '1':
            if not triggers:
                print_fast(f"{COLOR_ERROR}No triggers to select.{RESET_COLOR}")
                input("Press Enter to continue...")
                continue
            
            trigger_index = get_numeric_input("Enter the # of the trigger to select: ", int, min_val=1, max_val=len(triggers))
            selected_trigger = triggers[trigger_index - 1]
            return selected_trigger.get("id")

        elif choice == '2':
            new_trigger = add_trigger(config)
            if new_trigger:
                # add_trigger modifies the config object, now we save it.
                save_config(config)
                return new_trigger.get("id")
            # if new_trigger is None, it means creation was cancelled, so we loop again.

        elif choice == '0':
            return None
        
        else:
            print_fast(f"{COLOR_ERROR}Invalid choice.{RESET_COLOR}")
            input("Press Enter to continue...")
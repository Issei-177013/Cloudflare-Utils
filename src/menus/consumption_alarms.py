"""
Consumption Alarms Menu.

This module provides the user interface for managing consumption alarms.
Alarms are based on triggers and are used to notify the user when
traffic usage exceeds a certain limit.
"""
import uuid
from ..config import load_config, save_config
from ..display import display_as_table, print_fast, print_slow, COLOR_TITLE, COLOR_SEPARATOR, OPTION_SEPARATOR, RESET_COLOR, COLOR_WARNING, COLOR_ERROR, COLOR_SUCCESS, COLOR_INFO
from ..input_helper import get_user_input, get_numeric_input, get_validated_input
from ..logger import logger
from ..triggers import add_trigger as create_trigger
from .utils import clear_screen, confirm_action, select_from_list

def add_alarm():
    """Guides the user through adding a new consumption alarm."""
    config = load_config()
    
    print_fast(f"\n{COLOR_TITLE}--- Create New Consumption Alarm ---{RESET_COLOR}")
    
    alarm_name = get_user_input("Enter a name for this alarm (e.g., 'High download warning'):")
    
    # The trigger creation is now integrated into this flow.
    # This calls the `add_trigger` function from the triggers module,
    # but the user experience is seamless.
    new_trigger = create_trigger(config)

    if not new_trigger:
        print_fast(f"{COLOR_WARNING}Alarm creation cancelled because the trigger was not configured.{RESET_COLOR}")
        return

    new_alarm = {
        "id": f"alarm_{uuid.uuid4().hex[:8]}",
        "name": alarm_name,
        "trigger_id": new_trigger["id"]
    }

    if "alarms" not in config:
        config["alarms"] = []
    config["alarms"].append(new_alarm)
    
    save_config(config)
    logger.info(f"Created new consumption alarm '{alarm_name}' linked to trigger '{new_trigger['id']}'")
    print_fast(f"\n{COLOR_SUCCESS}✅ Alarm '{alarm_name}' created successfully.{RESET_COLOR}")

def list_alarms():
    """Lists all configured consumption alarms."""
    config = load_config()
    alarms = config.get("alarms", [])
    triggers = config.get("triggers", [])

    if not alarms:
        print_fast(f"{COLOR_WARNING}No consumption alarms configured.{RESET_COLOR}")
        return

    def get_trigger_details(trigger_id):
        for t in triggers:
            if t["id"] == trigger_id:
                return f"{t['name']} (Agent: {t['agent_name']})"
        return "Unknown/Deleted Trigger"

    headers = ["#", "Alarm Name", "Trigger"]
    rows = []
    for i, alarm in enumerate(alarms):
        rows.append([
            i + 1,
            alarm["name"],
            get_trigger_details(alarm["trigger_id"])
        ])
    
    print_fast(f"\n{COLOR_TITLE}--- Configured Consumption Alarms ---{RESET_COLOR}")
    display_as_table(rows, headers)

def delete_alarm():
    """Guides the user through deleting a consumption alarm."""
    config = load_config()
    alarms = config.get("alarms", [])

    if not alarms:
        print_fast(f"{COLOR_WARNING}No alarms to delete.{RESET_COLOR}")
        return

    print_fast("\nSelect an alarm to delete:")
    selected_alarm = select_from_list(alarms, "Select an alarm:")
    
    if not selected_alarm:
        return

    if confirm_action(f"Are you sure you want to delete the alarm '{selected_alarm['name']}'?"):
        config["alarms"].remove(selected_alarm)
        save_config(config)
        logger.info(f"Deleted alarm '{selected_alarm['name']}'")
        print_fast(f"{COLOR_SUCCESS}✅ Alarm deleted successfully.{RESET_COLOR}")


def consumption_alarms_menu():
    """Main menu for managing consumption alarms."""
    while True:
        clear_screen()
        print_fast(f"{COLOR_TITLE}--- Consumption Alarms ---{RESET_COLOR}")
        list_alarms()
        
        print_fast("\n1. Add New Alarm")
        print_fast("2. Edit an Alarm")
        print_fast("3. Delete an Alarm")
        print_fast("0. Back to Traffic Monitoring Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = get_user_input("Enter your choice: ")

        if choice == '1':
            add_alarm()
            input("\nPress Enter to continue...")
        elif choice == '2':
            print_fast(f"\n{COLOR_INFO}This feature is not yet implemented.{RESET_COLOR}")
            input("\nPress Enter to continue...")
        elif choice == '3':
            delete_alarm()
            input("\nPress Enter to continue...")
        elif choice == '0':
            break
        else:
            print_fast(f"{COLOR_ERROR}Invalid choice.{RESET_COLOR}")
            input("\nPress Enter to continue...")
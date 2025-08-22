"""
Menu for Trigger Management.
"""
from ..core.config import config_manager
from ..core.triggers import get_triggers, save_triggers, add_trigger as core_add_trigger, update_trigger, delete_trigger_by_id
from ..display import (
    display_as_table, print_fast, print_slow,
    COLOR_TITLE, COLOR_SEPARATOR, OPTION_SEPARATOR, RESET_COLOR,
    COLOR_WARNING, COLOR_ERROR, COLOR_SUCCESS, COLOR_INFO
)
from .utils import (
    clear_screen, select_from_list, confirm_action,
    get_user_input, get_numeric_input, get_validated_input
)
from ..core.logger import logger


def list_triggers_menu():
    """Displays a list of all configured triggers."""
    triggers = get_triggers()
    if not triggers:
        print_fast(f"{COLOR_WARNING}No triggers configured.{RESET_COLOR}")
        return

    headers = ["#", "Name", "Agent", "Period", "Volume (GB)", "Type", "Alerting"]
    rows = []
    for i, trigger in enumerate(triggers):
        alert_status = f"{COLOR_SUCCESS}On{RESET_COLOR}" if trigger.get('alert_enabled', True) else f"{COLOR_ERROR}Off{RESET_COLOR}"
        rows.append([
            i + 1,
            trigger.get('name'),
            trigger.get('agent_name'),
            trigger.get('period'),
            trigger.get('volume_gb'),
            trigger.get('volume_type'),
            alert_status
        ])
    
    print_fast(f"\n{COLOR_TITLE}--- Configured Triggers ---{RESET_COLOR}")
    display_as_table(rows, headers)

def add_trigger_menu():
    """Guides the user through creating a new trigger."""
    config = config_manager.get_config()
    print_fast(f"\n{COLOR_TITLE}--- Create New Trigger ---{RESET_COLOR}")

    agents = config.get("agents", [])
    self_monitor_config = config.get("self_monitor", {})
    if self_monitor_config.get("enabled"):
        agents.insert(0, {"name": self_monitor_config.get("name", "Self-Monitor"), "type": "self"})

    if not agents:
        print_fast(f"{COLOR_ERROR}No agents configured or self-monitor enabled. Please add an agent first.{RESET_COLOR}")
        return
    
    agent_to_monitor = select_from_list(agents, "Select the agent this trigger will monitor:")
    if not agent_to_monitor:
        return

    name = get_user_input("Enter a name for this trigger:")
    period_options = {'1': 'd', '2': 'w', '3': 'm'}
    period_choice = get_validated_input("Select period (1. Daily, 2. Weekly, 3. Monthly): ", lambda x: x in period_options, "Invalid choice.")
    period = period_options[period_choice]
    volume_gb = get_numeric_input("Enter traffic volume threshold in GB:", float)
    type_options = {'1': 'rx', '2': 'tx', '3': 'total'}
    type_choice = get_validated_input("Select volume type (1. RX, 2. TX, 3. Total): ", lambda x: x in type_options, "Invalid choice.")
    volume_type = type_options[type_choice]

    core_add_trigger(name, agent_to_monitor["name"], period, volume_gb, volume_type)
    print_fast(f"\n{COLOR_SUCCESS}✅ Trigger '{name}' created successfully.{RESET_COLOR}")

def edit_trigger_menu():
    """Guides the user through editing an existing trigger."""
    triggers = get_triggers()
    if not triggers:
        print_fast(f"{COLOR_WARNING}No triggers to edit.{RESET_COLOR}")
        return

    list_triggers_menu()
    choice = get_numeric_input("\nEnter the # of the trigger to edit (or 0 to cancel):", int, min_val=0, max_val=len(triggers))
    if choice == 0:
        return

    trigger_to_edit = triggers[choice - 1]
    print_fast(f"\n--- Editing Trigger: {trigger_to_edit['name']} ---")
    print_fast("Press Enter to keep the current value.")

    new_name = get_user_input(f"Name [{trigger_to_edit['name']}]:", default=trigger_to_edit['name'])
    new_volume_gb = get_numeric_input(f"Volume GB [{trigger_to_edit['volume_gb']}]:", float, default=trigger_to_edit['volume_gb'])
    current_alert_status = 'on' if trigger_to_edit.get('alert_enabled', True) else 'off'
    alert_choice = get_validated_input(f"Enable alerts? (on/off) [{current_alert_status}]:", lambda x: x.lower() in ['on', 'off', ''], "Invalid input.", default=current_alert_status)

    update_data = {
        "name": new_name,
        "volume_gb": new_volume_gb,
        "alert_enabled": alert_choice.lower() == 'on'
    }
    
    update_trigger(trigger_to_edit['id'], update_data)
    print_fast(f"\n{COLOR_SUCCESS}✅ Trigger '{new_name}' updated successfully.{RESET_COLOR}")

def delete_trigger_menu():
    """Guides the user through deleting a trigger."""
    triggers = get_triggers()
    if not triggers:
        print_fast(f"{COLOR_WARNING}No triggers to delete.{RESET_COLOR}")
        return

    list_triggers_menu()
    choice = get_numeric_input("\nEnter the # of the trigger to delete (or 0 to cancel):", int, min_val=0, max_val=len(triggers))
    if choice == 0:
        return

    trigger_to_delete = triggers[choice - 1]
    if confirm_action(f"Are you sure you want to delete the trigger '{trigger_to_delete['name']}'?"):
        delete_trigger_by_id(trigger_to_delete['id'])
        print_fast(f"{COLOR_SUCCESS}✅ Trigger deleted successfully.{RESET_COLOR}")

def trigger_management_menu():
    """Main menu for managing triggers."""
    while True:
        clear_screen()
        print_fast(f"{COLOR_TITLE}--- Trigger Management ---{RESET_COLOR}")
        list_triggers_menu()
        
        print_fast("\n1. Add New Trigger")
        print_fast("2. Edit a Trigger")
        print_fast("3. Delete a Trigger")
        print_fast("0. Back to Traffic Monitoring Menu")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = get_user_input("Enter your choice: ")

        if choice == '1':
            add_trigger_menu()
        elif choice == '2':
            edit_trigger_menu()
        elif choice == '3':
            delete_trigger_menu()
        elif choice == '0':
            break
        else:
            logger.warning(f"Invalid choice in trigger menu: {choice}")
            print_fast(f"{COLOR_ERROR}Invalid choice.{RESET_COLOR}")
        
        if choice in ['1', '2', '3']:
            input("\nPress Enter to continue...")

def select_trigger():
    """
    Displays a UI for selecting an existing trigger or creating a new one.
    Returns the ID of the selected or newly created trigger.
    """
    while True:
        clear_screen()
        print_fast(f"{COLOR_TITLE}--- Select a Trigger ---{RESET_COLOR}")
        list_triggers_menu()

        print_fast("\n1. Select an existing trigger")
        print_fast("2. Create a new trigger")
        print_fast("0. Cancel")
        print_fast(f"{COLOR_SEPARATOR}{OPTION_SEPARATOR}{RESET_COLOR}")

        choice = get_user_input("Enter your choice: ")

        if choice == '1':
            triggers = get_triggers()
            if not triggers:
                print_fast(f"{COLOR_ERROR}No triggers to select.{RESET_COLOR}")
                input("Press Enter to continue...")
                continue
            
            trigger_index = get_numeric_input("Enter the # of the trigger to select: ", int, min_val=1, max_val=len(triggers))
            selected_trigger = triggers[trigger_index - 1]
            return selected_trigger.get("id")

        elif choice == '2':
            add_trigger_menu()
            # After adding, we need to re-fetch to let the user select the new one
            continue

        elif choice == '0':
            return None
        
        else:
            print_fast(f"{COLOR_ERROR}Invalid choice.{RESET_COLOR}")
            input("Press Enter to continue...")
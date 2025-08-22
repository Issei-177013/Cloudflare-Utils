"""
Core Trigger Management Logic.

This module provides the business logic for managing triggers in the configuration.
It handles loading, saving, and manipulating trigger data without any
presentation-layer code.
"""
import uuid
from .config import config_manager
from .logger import logger

def get_triggers():
    """Loads the triggers from the main configuration file."""
    config = config_manager.get_config()
    return config.get("triggers", [])

def save_triggers(triggers):
    """Saves the triggers to the main configuration file."""
    config = config_manager.get_config()
    config["triggers"] = triggers
    config_manager.save_config()

def add_trigger(name, agent_name, period, volume_gb, volume_type, alert_enabled=True):
    """
    Adds a new trigger to the configuration.

    Args:
        name (str): The name of the trigger.
        agent_name (str): The name of the agent to monitor.
        period (str): The trigger period ('d', 'w', 'm').
        volume_gb (float): The traffic volume threshold in GB.
        volume_type (str): The volume type to monitor ('rx', 'tx', 'total').
        alert_enabled (bool): Whether to enable alerts for this trigger.

    Returns:
        dict: The newly created trigger.
    """
    new_trigger = {
        "id": f"trigger_{uuid.uuid4().hex[:8]}",
        "name": name,
        "agent_name": agent_name,
        "period": period,
        "volume_gb": volume_gb,
        "volume_type": volume_type,
        "alert_enabled": alert_enabled
    }

    triggers = get_triggers()
    triggers.append(new_trigger)
    save_triggers(triggers)
    
    logger.info(f"Added new trigger '{name}' ({new_trigger['id']})")
    return new_trigger

def update_trigger(trigger_id, new_data):
    """
    Updates an existing trigger with new data.
    """
    triggers = get_triggers()
    for i, trigger in enumerate(triggers):
        if trigger["id"] == trigger_id:
            triggers[i].update(new_data)
            save_triggers(triggers)
            logger.info(f"Updated trigger '{trigger['name']}' ({trigger_id})")
            return True
    return False

def delete_trigger_by_id(trigger_id):
    """
    Deletes a trigger from the configuration by its ID.
    """
    triggers = get_triggers()
    original_len = len(triggers)
    triggers = [t for t in triggers if t.get("id") != trigger_id]
    
    if len(triggers) < original_len:
        save_triggers(triggers)
        logger.info(f"Deleted trigger with ID {trigger_id}")
        return True
    return False
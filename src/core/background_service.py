"""
Background service for continuous monitoring of agent triggers.
"""
import time
import threading
import requests
from datetime import datetime
from .config import config_manager
from .logger import logger
from . import self_monitor
from .state_manager import load_state, save_state

# The interval in seconds for how often the background service runs.
SERVICE_INTERVAL_SECONDS = 300  # 5 minutes

def _get_usage_for_period(agent, period):
    """
    Fetches the latest usage data for an agent for a given period.
    Returns a dictionary with rx, tx, and total bytes, or None on error.
    """
    data = []
    if agent.get("type") == "self":
        result = self_monitor.get_usage_by_period(agent["vnstat_interface"], period)
        if "error" in result:
            logger.error(f"Error fetching self-monitor usage: {result['error']}")
            return None
        data = result.get('data', [])
    else:
        try:
            response = requests.get(
                f"{agent['url']}/usage_by_period",
                headers={"X-API-Key": agent["api_key"]},
                params={'period': period},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json().get('data', [])
            else:
                logger.error(f"Error fetching usage for {agent['name']}: {response.status_code}")
                return None
        except requests.RequestException as e:
            logger.error(f"Could not connect to agent {agent['name']}: {e}")
            return None

    if not data:
        return None

    latest_entry = data[-1]
    rx_bytes = latest_entry.get('rx', 0)
    tx_bytes = latest_entry.get('tx', 0)
    
    return {
        "rx": rx_bytes,
        "tx": tx_bytes,
        "total": rx_bytes + tx_bytes
    }

def _get_agent_by_name(config, agent_name):
    """Finds an agent configuration by name."""
    for agent in config.get("agents", []):
        if agent["name"] == agent_name:
            return agent
    # Handle self-monitor case
    self_monitor_config = config.get("self_monitor", {})
    if self_monitor_config.get("enabled") and self_monitor_config.get("name") == agent_name:
        return {
            "name": self_monitor_config.get("name"),
            "type": "self",
            "vnstat_interface": self_monitor_config.get("vnstat_interface")
        }
    return None

def _check_all_triggers():
    """
    Loads all triggers and evaluates them.
    """
    config = config_manager.get_config()
    triggers = config.get("triggers", [])
    
    if not triggers:
        logger.info("No triggers configured. Skipping check.")
        return

    for trigger in triggers:
        logger.debug(f"Checking trigger: {trigger['name']}")
        agent = _get_agent_by_name(config, trigger["agent_name"])
        
        if not agent:
            logger.warning(f"Agent '{trigger['agent_name']}' for trigger '{trigger['name']}' not found. Skipping.")
            continue
        
        usage_data = _get_usage_for_period(agent, trigger["period"])
        if usage_data is None:
            logger.warning(f"Could not get usage for agent {agent['name']}. Skipping trigger '{trigger['name']}'.")
            continue

        volume_gb = trigger.get("volume_gb", 0)
        volume_bytes = volume_gb * (1024**3)
        volume_type = trigger.get("volume_type", "total")
        actual_usage_bytes = usage_data.get(volume_type, 0)

        if actual_usage_bytes > volume_bytes:
            state = load_state()
            fired_triggers = state.get("fired_triggers", {})
            
            if not _has_trigger_fired_for_period(trigger, fired_triggers):
                logger.info(f"🔥 TRIGGER ACTIVATED: '{trigger['name']}' ({trigger['id']})")
                
                # --- Handle Actions ---
                # 1. Log alert if enabled
                if trigger.get('alert_enabled', True):
                    logger.warning(f"🚨 ALERT: Trigger '{trigger['name']}' has been activated. 🚨")
                    # In the future, this would call a notification function.
                else:
                    logger.info(f"Trigger '{trigger['name']}' is silent. No alert sent.")

                # --- Update State ---
                fired_triggers[trigger["id"]] = datetime.now().isoformat()
                state["fired_triggers"] = fired_triggers
                save_state(state)
            else:
                logger.debug(f"Trigger '{trigger['name']}' has already fired for this period.")

def _has_trigger_fired_for_period(trigger, fired_triggers):
    """
    Checks if a trigger has already been fired within its defined period.
    """
    trigger_id = trigger["id"]
    period = trigger["period"]
    last_fired_iso = fired_triggers.get(trigger_id)

    if not last_fired_iso:
        return False

    try:
        last_fired_dt = datetime.fromisoformat(last_fired_iso)
        now = datetime.now()

        if period == 'd':
            return last_fired_dt.date() == now.date()
        elif period == 'w':
            return last_fired_dt.isocalendar()[1] == now.isocalendar()[1] and last_fired_dt.year == now.year
        elif period == 'm':
            return last_fired_dt.month == now.month and last_fired_dt.year == now.year
        else:
            logger.warning(f"Unsupported period '{period}' in state check for trigger '{trigger_id}'. Allowing trigger.")
            return False
            
    except ValueError:
        logger.error(f"Could not parse timestamp for trigger '{trigger_id}'. Allowing trigger to fire.")
        return False


def run_background_service():
    """
    The main loop for the background service that periodically checks agent triggers.
    """
    logger.info("Background service started.")
    while True:
        try:
            logger.info("Running trigger checks...")
            _check_all_triggers()
            logger.info(f"Trigger checks complete. Waiting for {SERVICE_INTERVAL_SECONDS} seconds.")
            time.sleep(SERVICE_INTERVAL_SECONDS)
        
        except Exception as e:
            logger.error(f"An unexpected error occurred in the background service: {e}", exc_info=True)
            time.sleep(60)
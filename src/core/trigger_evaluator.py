"""
Evaluates agent triggers based on traffic usage.
"""

from .config import config_manager
from .state_manager import load_state, save_state
from .logger import logger
from . import self_monitor
import requests
from datetime import datetime

def _get_usage_for_period(agent, period):
    """
    Fetches the latest usage data for an agent for a given period.
    Returns a dictionary with rx, tx, and total bytes, or None on error.
    """
    data = []
    if agent.get("type") == "self":
        config = config_manager.get_config()
        interface = config.get("self_monitor", {}).get("vnstat_interface")
        result = self_monitor.get_usage_by_period(interface, period)
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

def check_triggers_for_agent(agent):
    """
    Checks all triggers for a given agent and takes action if they are met.
    """
    logger.info(f"Checking triggers for agent: {agent['name']}")
    
    triggers = agent.get("triggers", [])
    if not triggers:
        return

    for trigger in triggers:
        logger.debug(f"Evaluating trigger: {trigger['name']} for agent {agent['name']}")
        
        period = trigger.get("period")
        if not period:
            logger.warning(f"Trigger '{trigger['name']}' has no period defined. Skipping.")
            continue
            
        usage_data = _get_usage_for_period(agent, period)

        if usage_data is None:
            logger.warning(f"Could not get usage data for agent {agent['name']} for period '{period}'. Skipping trigger.")
            continue

        volume_gb = trigger.get("volume_gb", 0)
        volume_bytes = volume_gb * (1024**3)
        volume_type = trigger.get("volume_type", "total")

        actual_usage_bytes = usage_data.get(volume_type, 0)

        if actual_usage_bytes > volume_bytes:
            state = load_state()
            trigger_key = f"trigger_{agent['name']}_{trigger['name']}"

            # TODO: Implement _has_trigger_fired_for_period
            if not _has_trigger_fired_for_period(trigger_key, period, state):
                logger.info(f"🔥 TRIGGER ACTIVATED: '{trigger['name']}' for agent '{agent['name']}'")
                
                # Here we would dispatch the action, e.g., send_alarm() or rotate_ip()
                # For now, we just log it.
                logger.info(f"Action to perform: {trigger.get('action')}")

                state[trigger_key] = datetime.now().isoformat()
                save_state(state)
            else:
                logger.info(f"Trigger '{trigger['name']}' for agent '{agent['name']}' already fired for this period.")

def _has_trigger_fired_for_period(trigger_key, period, state):
    """
    Checks if a trigger has already been fired within the current period.
    """
    last_fired_iso = state.get(trigger_key)
    if not last_fired_iso:
        return False

    try:
        last_fired_dt = datetime.fromisoformat(last_fired_iso)
        now = datetime.now()

        if period == 'd': # Daily
            return last_fired_dt.date() == now.date()
        elif period == 'w': # Weekly
            return last_fired_dt.isocalendar()[1] == now.isocalendar()[1] and \
                   last_fired_dt.year == now.year
        elif period == 'm': # Monthly
            return last_fired_dt.month == now.month and \
                   last_fired_dt.year == now.year
        else:
            # For unknown or unsupported periods, assume it can always fire
            # to avoid blocking triggers indefinitely.
            logger.warning(f"Unsupported period '{period}' in state check. Allowing trigger.")
            return False
            
    except ValueError:
        logger.error(f"Could not parse timestamp '{last_fired_iso}' for trigger '{trigger_key}'. Allowing trigger to fire.")
        return False
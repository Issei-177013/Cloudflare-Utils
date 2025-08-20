"""
Background service for continuous monitoring of agent triggers.
"""

import time
import threading
from .config import load_config
from .logger import logger
from .menus.traffic_monitoring import get_all_agents
from .trigger_evaluator import check_triggers_for_agent

# The interval in seconds for how often the background service runs.
SERVICE_INTERVAL_SECONDS = 300  # 5 minutes

def run_background_service():
    """
    The main loop for the background service that periodically checks agent triggers.
    """
    logger.info("Background service started.")
    while True:
        try:
            logger.info("Running trigger checks for all agents...")
            
            all_agents = get_all_agents()
            if not all_agents:
                logger.info("No agents configured. Skipping trigger checks.")
            else:
                for agent in all_agents:
                    check_triggers_for_agent(agent)
            
            logger.info(f"Trigger checks complete. Waiting for {SERVICE_INTERVAL_SECONDS} seconds.")
            time.sleep(SERVICE_INTERVAL_SECONDS)
        
        except Exception as e:
            logger.error(f"An unexpected error occurred in the background service: {e}")
            # Wait a bit before retrying to avoid rapid-fire errors
            time.sleep(60)
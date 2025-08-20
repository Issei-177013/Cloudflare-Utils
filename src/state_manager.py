import json
import os
from logger import logger

STATE_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.cfutils-state.json'))

def load_state():
    """Loads the state from the .cfutils-state.json file."""
    if not os.path.exists(STATE_FILE_PATH):
        logger.info(f"State file not found at {STATE_FILE_PATH}. Creating a new one.")
        save_state({"global_rotations": {}})
        return {"global_rotations": {}}
    try:
        with open(STATE_FILE_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Could not decode JSON from {STATE_FILE_PATH}. Returning default state.")
        return {"global_rotations": {}}

def save_state(data):
    """Saves the state data to the .cfutils-state.json file."""
    try:
        with open(STATE_FILE_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save state to {STATE_FILE_PATH}: {e}")
        return False

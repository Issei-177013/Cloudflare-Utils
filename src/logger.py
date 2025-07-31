import logging
import os
from logging.handlers import RotatingFileHandler
from pythonjsonlogger.json import JsonFormatter
from colorlog import ColoredFormatter

# Define the custom logger name
LOGGER_NAME = "CloudflareUtils"

# --- Directory Setup ---
# Determine the base directory of the project
# Assumes this file is in 'src/logger.py'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# --- Formatter Definitions ---
# Standard formatter for console logs
CONSOLE_FORMAT = '%(log_color)s%(levelname)s:%(name)s:%(message)s'
# Standard formatter for file logs
FILE_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s'

class CustomJsonFormatter(JsonFormatter):
    """
    Custom JSON formatter to add the module name to the log record.
    """
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['module'] = record.module

# JSON formatter for production logs
JSON_FORMAT = '%(asctime)s %(name)s %(levelname)s %(module)s %(message)s'


def setup_logger(
    name=LOGGER_NAME,
    console_level=logging.INFO,
    file_level=logging.DEBUG,
    log_file="app.log",
    log_format=None
):
    """
    Sets up a flexible and unified logger for the application.

    Args:
        name (str): The name of the logger.
        console_level (int): The logging level for the console handler.
        file_level (int): The logging level for the file handler.
        log_file (str): The name of the log file.
        log_format (str, optional): The log format to use ('json' or None).
                                    Defaults to os.environ.get("LOG_FORMAT").

    Returns:
        logging.Logger: The configured logger instance.
    """
    # Create the logs directory if it doesn't exist.
    # This is done here to make the module import more side-effect-free.
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
        
    logger = logging.getLogger(name)
    
    # Prevent adding handlers multiple times
    if logger.hasHandlers():
        # Clear existing handlers to allow reconfiguration for tests
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # Set the overall logger level to the lowest of the handlers
    logger.setLevel(min(console_level, file_level))

    # --- Console Handler (for human-readable, colored output) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_formatter = ColoredFormatter(CONSOLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # --- File Handler (for detailed, rotating logs) ---
    log_file_path = os.path.join(LOGS_DIR, log_file)
    # Rotate files at 10 MB, keep 5 backups
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(file_level)

    # Determine which formatter to use for the file handler
    log_format_env = log_format or os.environ.get("LOG_FORMAT")
    if log_format_env and log_format_env.lower() == 'json':
        file_formatter = CustomJsonFormatter(JSON_FORMAT)
    else:
        file_formatter = logging.Formatter(FILE_FORMAT)
    
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Do not propagate to the root logger to avoid duplicate messages
    logger.propagate = False

    return logger

def disable_for_tests():
    """
    Disables logging for the application, typically for unit tests.
    This sets the logger's level to a value higher than CRITICAL.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.CRITICAL + 1)

# --- Singleton Logger Instance ---
# A single logger for the entire application, configured on import.
# The `app.py` and other modules can `from .logger import logger`.
logger = setup_logger()
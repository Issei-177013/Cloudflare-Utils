import logging
import os
import coloredlogs
from logging.handlers import TimedRotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

def setup_logger(log_file="app.log", level=logging.INFO, propagate=False):
    """
    Sets up a unified logger for the application.
    """
    logger = logging.getLogger("CloudflareUtils")
    
    if logger.hasHandlers():
        return logger

    log_file_path = os.path.join(LOGS_DIR, log_file)
    file_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=7)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.propagate = propagate

    # Add coloredlogs to the logger for file logging
    coloredlogs.install(level=level, logger=logger, fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add a stream handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING) # Only show warnings and errors on console
    console_formatter = coloredlogs.ColoredFormatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger

# A single logger for the entire application
logger = setup_logger()

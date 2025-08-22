"""
Logger Configuration.

This module sets up the logging infrastructure for the application. It configures
a file logger with daily rotation and an optional, colored console logger.
"""
import logging
import os
import sys
import coloredlogs
from logging.handlers import TimedRotatingFileHandler
from threading import Lock

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

# --- Singleton Logger Setup ---
_logger_instance = None
_logger_lock = Lock()

def get_logger():
    """
    Returns a singleton logger instance for the application.
    """
    global _logger_instance
    if _logger_instance is None:
        with _logger_lock:
            if _logger_instance is None:
                _logger_instance = setup_logger()
    return _logger_instance

def setup_logger(log_file="app.log", level=logging.INFO):
    """
    Configures and returns the main application logger.

    This function is called once to create the singleton logger instance.
    It sets up a rotating file handler and can be extended to add other
    handlers (e.g., console).
    """
    logger = logging.getLogger("CloudflareUtils")
    logger.setLevel(level)
    logger.propagate = False

    # Prevent adding handlers if they already exist
    if logger.hasHandlers():
        return logger

    # File Handler
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
        
    log_file_path = os.path.join(LOGS_DIR, log_file)
    file_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=7)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    # Optional: Redirect stdout/stderr for non-interactive execution
    if os.environ.get('LOG_TO_FILE') == 'true':
        sys.stdout = StreamToLogger(logger, logging.INFO)
        sys.stderr = StreamToLogger(logger, logging.ERROR)
        logger.info("Logger initialized for file output.")
    else:
        logger.info("Logger initialized for interactive output.")
        
    return logger

def configure_console_logging(config):
    """
    Adds or removes a colored console handler based on the application config.
    """
    logger = get_logger()
    
    # Remove any existing console handler to avoid duplicates
    console_handler = None
    for handler in logger.handlers:
        if isinstance(handler, coloredlogs.StandardErrorHandler):
            console_handler = handler
            break
    
    if console_handler:
        logger.removeHandler(console_handler)

    # Add a new console handler if enabled in the config
    if config.get("settings", {}).get("console_logging", True):
        coloredlogs.install(level='INFO', logger=logger, fmt='%(levelname)s: %(message)s')

class StreamToLogger:
    """
    A file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass

# Initialize and expose the logger instance
logger = get_logger()
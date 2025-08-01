import logging
import os
import sys
import coloredlogs
from logging.handlers import TimedRotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

class StreamToLogger:
    """
    Fake file-like stream object that redirects writes to a logger instance.
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

def setup_logger(log_file="app.log", level=logging.INFO, propagate=False):
    """
    Sets up a unified logger for the application.
    Redirects stdout and stderr to the logger to capture all output.
    """
    logger = logging.getLogger("CloudflareUtils")
    
    # Prevent adding handlers multiple times
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)
    logger.propagate = propagate

    # File Handler - Timed rotation, plain text
    log_file_path = os.path.join(LOGS_DIR, log_file)
    file_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=7)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    # Console Handler - Colored output for interactive use, warnings and above
    # This remains useful for direct script execution, e.g., `cf-utils.py`
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING) 
    console_formatter = coloredlogs.ColoredFormatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Redirect stdout and stderr to the logger.
    # This is crucial for capturing all output from cron jobs.
    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)
    
    logger.info("Logger initialized. stdout and stderr are now redirected to the log file.")

    return logger

# A single logger for the entire application
logger = setup_logger()

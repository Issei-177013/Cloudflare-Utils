import logging
import os
import sys
import coloredlogs
from logging.handlers import TimedRotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

# Ensure the logs directory exists
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
    Sets up the file logger for the application.
    """
    logger = logging.getLogger("CloudflareUtils")

    # Initial setup (only done once)
    if not logger.handlers:
        logger.setLevel(level)
        logger.propagate = propagate

        # File Handler
        log_file_path = os.path.join(LOGS_DIR, log_file)
        file_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=7)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

        # stdout/stderr redirection for non-interactive mode
        if os.environ.get('LOG_TO_FILE') == 'true':
            sys.stdout = StreamToLogger(logger, logging.INFO)
            sys.stderr = StreamToLogger(logger, logging.ERROR)
            logger.info("Logger initialized for file output.")
        else:
            logger.info("Logger initialized for interactive output.")

    return logger

def configure_console_logging(config):
    """
    Sets up or reconfigures the console logger based on the provided configuration.
    """
    logger = logging.getLogger("CloudflareUtils")

    # Console handler reconfiguration
    # Remove any existing console handler (a StreamHandler that is not a FileHandler)
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

    # Add console handler based on config
    if config.get("settings", {}).get("console_logging", True):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = coloredlogs.ColoredFormatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

# A single logger for the entire application, initialized with file logging
logger = setup_logger()
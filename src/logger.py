"""
Logger Configuration.

This module sets up the logging infrastructure for the application. It configures
a file logger with daily rotation and an optional, colored console logger.
It also provides a mechanism to redirect stdout and stderr to the log file,
which is useful for non-interactive script execution (e.g., cron jobs).
"""
import logging
import os
import sys
import coloredlogs
from logging.handlers import TimedRotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

class StreamToLogger:
    """
    A file-like stream object that redirects writes to a logger instance.

    This class is used to redirect standard output and standard error to the
    logging system, allowing capture of all output from scripts and libraries
    that write directly to `sys.stdout` or `sys.stderr`.

    Attributes:
        logger (logging.Logger): The logger instance to which messages are sent.
        level (int): The logging level to use for the messages.
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ''

    def write(self, buf):
        """
        Writes a buffer to the logger, splitting it into lines.

        Args:
            buf (str): The buffer to write.
        """
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        """
        A no-op flush method to satisfy the file-like object interface.
        """
        pass

def setup_logger(log_file="app.log", level=logging.INFO, propagate=False):
    """
    Sets up the root logger for the application.

    This function configures a timed rotating file handler. If the environment
    variable `LOG_TO_FILE` is set to 'true', it also redirects stdout and
    stderr to the logger. This setup is performed only once.

    Args:
        log_file (str, optional): The name of the log file. Defaults to "app.log".
        level (int, optional): The logging level. Defaults to logging.INFO.
        propagate (bool, optional): Whether to propagate logs to parent loggers.
                                    Defaults to False.

    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger("CloudflareUtils")

    if not logger.handlers:
        logger.setLevel(level)
        logger.propagate = propagate

        log_file_path = os.path.join(LOGS_DIR, log_file)
        file_handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=7)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

        if os.environ.get('LOG_TO_FILE') == 'true':
            sys.stdout = StreamToLogger(logger, logging.INFO)
            sys.stderr = StreamToLogger(logger, logging.ERROR)
            logger.info("Logger initialized for file output.")
        else:
            logger.info("Logger initialized for interactive output.")

    return logger

def configure_console_logging(config):
    """
    Configures the console logger based on application settings.

    This function adds or removes a colored console handler based on the
    `console_logging` setting in the configuration file. This allows the user
    to toggle console output on and off during runtime.

    Args:
        config (dict): The application configuration dictionary.
    """
    logger = logging.getLogger("CloudflareUtils")

    # Remove any existing console handler to avoid duplicates.
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

    # Add a new console handler if enabled in the config.
    if config.get("settings", {}).get("console_logging", True):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = coloredlogs.ColoredFormatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

# A single logger for the entire application, initialized with file logging
logger = setup_logger()
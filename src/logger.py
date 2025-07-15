import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as you want"""
    log_file_path = os.path.join(LOGS_DIR, log_file)
    handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=7)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False

    return logger

# Create loggers for different modules
app_logger = setup_logger('app', 'app.log')
cloudflare_api_logger = setup_logger('cloudflare_api', 'cloudflare_api.log')
dns_manager_logger = setup_logger('dns_manager', 'dns_manager.log')
config_logger = setup_logger('config', 'config.log')
input_helper_logger = setup_logger('input_helper', 'input_helper.log')
ip_rotator_logger = setup_logger('ip_rotator', 'ip_rotator.log')
validator_logger = setup_logger('validator', 'validator.log')

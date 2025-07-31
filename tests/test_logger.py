import os
import logging
import json
import unittest
from unittest.mock import patch, MagicMock

# We need to make sure the 'src' directory is in the python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.logger import setup_logger, disable_for_tests, LOGGER_NAME, LOGS_DIR

class TestLogger(unittest.TestCase):

    def setUp(self):
        # Ensure the logger is clean before each test
        logger = logging.getLogger(LOGGER_NAME)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        # Reset level
        logger.setLevel(logging.NOTSET)
        # Also remove the singleton logger instance from the module where it is defined
        # so that it gets re-created in each test.
        if 'src.logger' in sys.modules:
            del sys.modules['src.logger']


    @patch('src.logger.os.makedirs')
    @patch('src.logger.os.path.exists', return_value=False)
    @patch.dict(os.environ, {}, clear=True)
    def test_logger_creation_and_dir_creation(self, mock_exists, mock_makedirs):
        """Test that the logger is created and creates the log directory."""
        from src.logger import setup_logger, LOGS_DIR
        logger = setup_logger(name=LOGGER_NAME)
        
        mock_exists.assert_called_with(LOGS_DIR)
        mock_makedirs.assert_called_with(LOGS_DIR)

        self.assertEqual(len(logger.handlers), 2)
        
        console_handler = logger.handlers[0]
        file_handler = logger.handlers[1]

        self.assertIsInstance(console_handler, logging.StreamHandler)
        self.assertEqual(console_handler.level, logging.INFO)

        from logging.handlers import RotatingFileHandler
        self.assertIsInstance(file_handler, RotatingFileHandler)
        self.assertEqual(file_handler.level, logging.DEBUG)
        self.assertIsInstance(file_handler.formatter, logging.Formatter)

    @patch('src.logger.os.makedirs')
    @patch('src.logger.os.path.exists', return_value=True)
    @patch.dict(os.environ, {"LOG_FORMAT": "json"})
    def test_json_logging(self, mock_exists, mock_makedirs):
        """Test that file logging uses JSON format when LOG_FORMAT is 'json'."""
        from src.logger import setup_logger, CustomJsonFormatter
        logger = setup_logger(name=LOGGER_NAME)
        
        file_handler = logger.handlers[1]

        self.assertIsInstance(file_handler.formatter, CustomJsonFormatter)

    @patch('src.logger.os.makedirs')
    @patch('src.logger.os.path.exists', return_value=True)
    def test_disable_for_tests(self, mock_exists, mock_makedirs):
        """Test that logging can be disabled."""
        from src.logger import setup_logger, disable_for_tests
        logger = setup_logger(name=LOGGER_NAME)
        self.assertTrue(logger.isEnabledFor(logging.INFO))

        disable_for_tests()
        
        # Get the logger instance again to check its state
        logger_after_disable = logging.getLogger(LOGGER_NAME)
        self.assertFalse(logger_after_disable.isEnabledFor(logging.CRITICAL))
        self.assertEqual(logger_after_disable.level, logging.CRITICAL + 1)

if __name__ == '__main__':
    unittest.main()
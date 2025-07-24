"""Logging configuration for the LibreApp library."""
import logging
from typing import Tuple
import os
from datetime import datetime

def setup_logger() -> Tuple[logging.Logger, logging.Logger]:
    """
    Set up console and file loggers.
    
    Returns:
        Tuple of (console_logger, file_logger)
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Configure console logger
    console_log = logging.getLogger('console')
    if not console_log.handlers:  # Only add handler if none exists
        console_log.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        console_log.addHandler(console_handler)
    
    # Configure file logger
    file_log = logging.getLogger('file')
    if not file_log.handlers:  # Only add handler if none exists
        file_log.setLevel(logging.DEBUG)
        log_file = f"logs/libreapp_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_log.addHandler(file_handler)
    
    return console_log, file_log

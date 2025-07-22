import logging
import logging.handlers
import os
from datetime import datetime

def setup_logger(log_dir: str = "logs") -> tuple[logging.Logger, logging.Logger]:
    """
    Set up two loggers:
    1. console_logger: INFO level, prints to console
    2. file_logger: DEBUG level, logs everything to file
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (INFO level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # File handler (DEBUG level) with rotation
    log_file = os.path.join(log_dir, f"libreview_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Create loggers
    console_logger = logging.getLogger('libre_console')
    file_logger = logging.getLogger('libre_file')

    # Set levels
    console_logger.setLevel(logging.INFO)
    file_logger.setLevel(logging.DEBUG)

    # Add handlers
    console_logger.addHandler(console_handler)
    file_logger.addHandler(file_handler)

    # Prevent propagation to root logger
    console_logger.propagate = False
    file_logger.propagate = False

    return console_logger, file_logger

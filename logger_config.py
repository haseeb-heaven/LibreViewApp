import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Any, Dict
from http.client import HTTPConnection

class HTTPFormatter(logging.Formatter):
    """Custom formatter for HTTP request/response logging."""
    
    def format_http_message(self, record: logging.LogRecord) -> str:
        if not hasattr(record, 'http_data'):
            return record.msg
            
        data: Dict[str, Any] = record.http_data
        formatted_parts = []
        
        # Request information
        if 'request' in data:
            req = data['request']
            formatted_parts.extend([
                "REQUEST:",
                f"URL: {req.get('url', 'N/A')}",
                f"Method: {req.get('method', 'N/A')}",
                "Headers:",
                json.dumps(req.get('headers', {}), indent=2),
                "Body:",
                json.dumps(req.get('body', {}), indent=2) if req.get('body') else "None"
            ])
            
        # Response information
        if 'response' in data:
            resp = data['response']
            formatted_parts.extend([
                "\nRESPONSE:",
                f"Status: {resp.get('status_code', 'N/A')}",
                "Headers:",
                json.dumps(resp.get('headers', {}), indent=2),
                "Body:",
                json.dumps(resp.get('body', {}), indent=2) if resp.get('body') else "None"
            ])
            
        return "\n".join([record.msg] + formatted_parts)
    
    def format(self, record: logging.LogRecord) -> str:
        # Format the basic message
        basic_message = super().format(record)
        
        # Add HTTP details if available
        if hasattr(record, 'http_data'):
            return self.format_http_message(record)
        
        return basic_message

def setup_logger(log_dir: str = "logs") -> tuple[logging.Logger, logging.Logger]:
    """
    Set up two loggers:
    1. console_logger: INFO level, prints to console (clean, minimal output)
    2. file_logger: DEBUG level, logs everything to file (verbose, with HTTP details)
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Disable debug logging for http.client
    HTTPConnection.debuglevel = 0

    # Create formatters
    console_formatter = logging.Formatter(
        '%(message)s'  # Simplified console output
    )
    file_formatter = HTTPFormatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d][%(funcName)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (INFO level and above only, with strict filtering)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Create console filter for user-facing messages only
    class UserMessageFilter(logging.Filter):
        def filter(self, record):
            # Only allow INFO or higher messages that don't contain HTTP or debug data
            if record.levelno < logging.INFO:
                return False
            if hasattr(record, 'http_data'):
                return False
            if any(x in record.msg.lower() for x in ['request', 'response', 'header', 'body', 'url', 'debug']):
                return False
            return True
    
    console_handler.addFilter(UserMessageFilter())

    # File handler (DEBUG level) with rotation - gets everything
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

    # Set up root logger to catch all other debug messages
    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler])
    
    # Set levels (console logger is strictly INFO and above)
    console_logger.setLevel(logging.INFO)
    file_logger.setLevel(logging.DEBUG)

    # Add handlers
    console_logger.addHandler(console_handler)
    file_logger.addHandler(file_handler)

    # Prevent propagation
    console_logger.propagate = False
    file_logger.propagate = False

    # Disable other loggers that might print to console
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('http.client').setLevel(logging.WARNING)

    return console_logger, file_logger

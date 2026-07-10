"""
    Requirements:
    - colorama
    
    Add this to .env file:
    
    CONSOLE_LOG_LEVEL="INFO"
    FILE_LOG_FORMAT="%(asctime)s %(levelname)s %(message)s"
    CONSOLE_LOG_FORMAT="%(levelname)s %(message)s"
    
    Add configs/app_logger.json:
    {
        "log_folder": "logs",
        
        "muted_libs": [
            "List out what library to be muted here!"
        ]
    }
"""
import os
import json
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import logging
import logging.handlers

from colorama import Fore, Style

# == Load config file
config = {
    "log_folder": "logs",
    "muted_libs": [],
    "file_log_format": "%(asctime)s %(levelname)s %(message)s",
    "console_log_format": "%(levelname)s %(message)s"
}

# ==
class ColoredConsoleFormatter(logging.Formatter):
    COLOR_MAPPING = {
        logging.DEBUG: Fore.LIGHTBLACK_EX,
        logging.INFO: Fore.BLUE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        
        if isinstance(msg, dict):
            msg = json.dumps(msg, indent = 2)
        
        else:
            try:
                msg = str(msg)
                
            except Exception as e:
                msg = "Cannot convert message to string!"
                
        return f"{self.COLOR_MAPPING.get(record.levelno, '')}{record.levelname.ljust(5)} - {msg}{Style.RESET_ALL}"

# ==
def setup_logging():
    # Get log level from environment or config
    try:
        from src.configs import env_config
        console_log_level = env_config.console_log_level
        file_log_format = env_config.file_log_format
        console_log_format = env_config.console_log_format
    except ImportError:
        # Fallback if config not available
        console_log_level = os.environ.get("CONSOLE_LOG_LEVEL", "INFO")
        file_log_format = os.environ.get("FILE_LOG_FORMAT", "%(asctime)s %(levelname)s %(message)s")
        console_log_format = os.environ.get("CONSOLE_LOG_FORMAT", "%(levelname)s %(message)s")
    
    # ==
    log_folder = config.get("log_folder")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    
    # == File Handler
    file_handler = logging.handlers.RotatingFileHandler(
        filename = os.path.join(log_folder, "app.log"),
        maxBytes = 10 * 1024 * 1024, # 10MB
        backupCount = 5
    )
    
    file_handler.setFormatter(
        logging.Formatter(file_log_format)
    )
    
    file_handler.setLevel(logging.DEBUG)
    
    # == Console Handler
    console_handler = logging.StreamHandler()
    
    console_handler.setFormatter(
        ColoredConsoleFormatter(console_log_format)
    )
    
    # Convert string level to logging constant
    log_level = getattr(logging, console_log_level.upper(), logging.INFO)
    
    # ==
    logging.basicConfig(
        level=log_level,
        format=console_log_format,
        handlers=[console_handler, file_handler],
    )
    
    for muted_lib in config.get("muted_libs", []):
        logging.getLogger(muted_lib).setLevel(logging.WARNING)
"""Logging configuration for Ó bože."""
import logging
import sys
from pathlib import Path
from datetime import datetime

# Create logs directory
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log file with timestamp
LOG_FILE = LOGS_DIR / f"oboze_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


def setup_logging():
    """Configure logging to file and console."""
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Return app logger
    return logging.getLogger("oboze")


# Initialize logging
logger = setup_logging()
logger.info(f"Logging to: {LOG_FILE}")

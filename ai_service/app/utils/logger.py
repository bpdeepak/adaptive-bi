import os
from loguru import logger as loguru_logger
from datetime import datetime

# Remove default handler to avoid duplicate logs
loguru_logger.remove()

# Configure logger for console output
loguru_logger.add(
    sink="sys.stdout",
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
    diagnose=True
)

# Configure logger for file output
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file_path = os.path.join(LOG_DIR, f"ai_service_{datetime.now().strftime('%Y-%m-%d')}.log")

loguru_logger.add(
    sink=log_file_path,
    rotation="1 day",  # New log file every day
    retention="7 days", # Keep logs for 7 days
    compression="zip",  # Compress old log files
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    diagnose=True
)

# Expose loguru_logger as 'logger' for easy import
logger = loguru_logger
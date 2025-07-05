import os
import sys
from loguru import logger as loguru_logger
from datetime import datetime
import socket
from typing import Optional
import psutil
import gc

# Get service identifier information
SERVICE_NAME = "adaptive-bi-ai-service"
HOSTNAME = socket.gethostname()
PID = os.getpid()

# Remove default handler to avoid duplicate logs
loguru_logger.remove()

# Configure logger for console output
loguru_logger.add(
    sink=sys.stdout,  # Use actual sys.stdout, not string
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <blue>PID:{process}</blue> | <red>Host:{extra[hostname]}</red> | <magenta>{name}</magenta>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <yellow>Thread:{thread}</yellow> - <level>{message}</level>",
    colorize=True,
    diagnose=True
)

# Configure logger for file output - only if logs directory is writable
LOG_DIR = "logs"
if os.access(".", os.W_OK):  # Check if we can write to current directory
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_file_path = os.path.join(LOG_DIR, f"ai_service_{datetime.now().strftime('%Y-%m-%d')}.log")
        
        loguru_logger.add(
            sink=log_file_path,
            rotation="100 MB",  # Rotate when file gets too large to prevent memory issues
            retention="3 days", # Keep logs for only 3 days to save space
            compression="zip",  # Compress old log files
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | PID:{process} | Host:{extra[hostname]} | {name}:{function}:{line} | Thread:{thread} - {message}",
            diagnose=True,
            enqueue=True,  # Make logging thread-safe and memory efficient
            serialize=False  # Don't serialize to save memory
        )
    except PermissionError:
        # If file logging fails, just use console logging
        pass

# Expose loguru_logger as 'logger' for easy import with enhanced context
logger = loguru_logger.bind(
    service=SERVICE_NAME,
    hostname=HOSTNAME,
    pid=PID
)

# Add convenience methods for structured logging
def log_service_start():
    """Log service startup with full context"""
    logger.info(f"🚀 {SERVICE_NAME} starting up on {HOSTNAME} (PID: {PID})")

def log_service_stop():
    """Log service shutdown with full context"""
    logger.info(f"🛑 {SERVICE_NAME} shutting down on {HOSTNAME} (PID: {PID})")

def log_model_operation(operation: str, model_name: str, status: str, details: str = ""):
    """Log model operations with structured information"""
    logger.info(f"🤖 Model Operation | {operation} | {model_name} | Status: {status} | {details}")

def log_database_operation(operation: str, collection: str, status: str, count: Optional[int] = None, details: str = ""):
    """Log database operations with structured information"""
    count_info = f"Count: {count} | " if count is not None else ""
    logger.info(f"💾 DB Operation | {operation} | {collection} | Status: {status} | {count_info}{details}")

def log_api_request(method: str, endpoint: str, status_code: int, response_time: Optional[float] = None, user_id: Optional[str] = None):
    """Log API requests with structured information"""
    time_info = f"Time: {response_time:.3f}s | " if response_time is not None else ""
    user_info = f"User: {user_id} | " if user_id else ""
    logger.info(f"🌐 API Request | {method} {endpoint} | Status: {status_code} | {time_info}{user_info}")

def log_error_with_context(error: Exception, context: str = "", operation: str = ""):
    """Log errors with enhanced context"""
    operation_info = f"Operation: {operation} | " if operation else ""
    logger.error(f"❌ Error | {operation_info}{context} | Exception: {type(error).__name__}: {str(error)}")

def log_performance_metric(metric_name: str, value: float, unit: str = "", context: str = ""):
    """Log performance metrics"""
    unit_info = f" {unit}" if unit else ""
    context_info = f" | Context: {context}" if context else ""
    logger.info(f"📊 Performance | {metric_name}: {value}{unit_info}{context_info}")

def log_memory_usage(context=""):
    """Log current memory usage for debugging."""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # Log memory in MB
        rss_mb = memory_info.rss / 1024 / 1024
        vms_mb = memory_info.vms / 1024 / 1024
        
        logger.info(f"MEMORY {context}: RSS={rss_mb:.1f}MB, VMS={vms_mb:.1f}MB, %={memory_percent:.1f}%")
        
        # Force garbage collection if memory usage is high
        if memory_percent > 70:
            logger.warning(f"High memory usage detected ({memory_percent:.1f}%), forcing garbage collection")
            gc.collect()
            
    except Exception as e:
        logger.error(f"Error logging memory usage: {e}")

def force_memory_cleanup():
    """Aggressive memory cleanup."""
    try:
        # Force garbage collection multiple times
        for i in range(3):
            gc.collect()
        
        # Clear any lingering references
        if hasattr(gc, 'set_threshold'):
            gc.set_threshold(100, 10, 10)  # More aggressive GC
            
        logger.info("Forced memory cleanup completed")
    except Exception as e:
        logger.error(f"Error during memory cleanup: {e}")

# Export the enhanced logger as the main logger
__all__ = ['logger', 'log_service_start', 'log_service_stop', 'log_model_operation', 
           'log_database_operation', 'log_api_request', 'log_error_with_context', 'log_performance_metric', 'log_memory_usage']
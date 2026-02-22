import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger():
    """Configure application logging"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Main application logger
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.INFO)
    
    # Application log file (rotating, max 10MB, keep 5 backups)
    app_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_handler.setFormatter(detailed_formatter)
    app_logger.addHandler(app_handler)
    
    # Error logger (separate file for errors only)
    error_logger = logging.getLogger('error')
    error_logger.setLevel(logging.ERROR)
    
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setFormatter(detailed_formatter)
    error_logger.addHandler(error_handler)
    
    # Console handler (so we still see logs in terminal)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.INFO)
    
    app_logger.addHandler(console_handler)
    
    return app_logger, error_logger


# Initialize loggers
app_logger, error_logger = setup_logger()


def log_info(message):
    """Log info message"""
    app_logger.info(message)


def log_error(message, exception=None):
    """Log error message"""
    if exception:
        error_logger.error(f"{message} - Exception: {str(exception)}")
    else:
        error_logger.error(message)


def log_request(endpoint, method, status_code):
    """Log HTTP request"""
    app_logger.info(f"Request: {method} {endpoint} - Status: {status_code}")


def log_report_generation(success, filename=None, error=None):
    """Log report generation attempt"""
    if success:
        app_logger.info(f"✅ Report generated successfully: {filename}")
    else:
        error_logger.error(f"❌ Report generation failed: {error}")
"""
Logging utilities for the application.

This module provides functions for setting up and configuring logging.
"""

import logging
import sys
from typing import Any, Dict

from app.core.config import settings


def configure_logging() -> None:
    """
    Configure logging for the application.
    
    Sets up logging with the appropriate level and format.
    """
    log_format = settings.LOG_FORMAT
    log_level = getattr(logging, settings.LOG_LEVEL)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Set level for external libraries
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    # Log configuration details
    logging.info(f"Logging configured with level {settings.LOG_LEVEL}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Name for the logger
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_request_details(details: Dict[str, Any]) -> None:
    """
    Log details about a request.
    
    Args:
        details: Dictionary of request details to log
    """
    logger = get_logger("request")
    request_id = details.get("request_id", "unknown")
    method = details.get("method", "")
    path = details.get("path", "")
    status_code = details.get("status_code", "")
    
    logger.info(
        f"Request {request_id} | {method} {path} | Status: {status_code}"
    ) 
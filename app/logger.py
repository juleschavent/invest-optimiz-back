"""
Logging Configuration

Sets up structured logging for the application.
"""

import logging
import sys

from app.config import get_settings


def setup_logging() -> None:
    """
    Configure application logging.

    Sets up:
    - Log format with timestamp, level, module, and message
    - Log level from settings
    - Console output (stdout)
    - Proper formatting for development
    """
    settings = get_settings()

    # Define log format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=settings.log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)  # Log to console
        ],
    )

    # Set specific log levels for third-party libraries
    # (to avoid too much noise in development)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo else logging.WARNING
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Usage:
        from app.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")

    Args:
        name: Usually __name__ to get logger for current module

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

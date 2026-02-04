"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path

from ..config.settings import settings


def setup_logging() -> logging.Logger:
    """Set up application logging."""
    # Create logger
    logger = logging.getLogger("ab_testing_agent")
    logger.setLevel(getattr(logging, settings.log_level))

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(settings.log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if configured)
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setLevel(getattr(logging, settings.log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f"ab_testing_agent.{name}")


# Initialize default logger
default_logger = setup_logging()

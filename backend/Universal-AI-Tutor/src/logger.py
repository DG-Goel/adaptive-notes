"""
Logging configuration for Universal AI Tutor.

Provides structured JSON logging with request IDs and context.
"""

import logging
import sys
from typing import Any

from src.config import get_settings


def setup_logging() -> None:
    """
    Configure application logging.

    Sets up structured logging with appropriate format and level.
    """
    settings = get_settings()

    # Create logger
    logger = logging.getLogger("universal_ai_tutor")
    logger.setLevel(settings.log_level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.log_level)

    # Create formatter
    if settings.app_env == "production":
        # JSON format for production
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s"}'
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger: Configured logger instance
    """
    return logging.getLogger(f"universal_ai_tutor.{name}")


# Initialize logging on module import
setup_logging()

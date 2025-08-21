"""Logging utilities for the Demo Agent."""

import logging
import sys
from typing import Optional

from ..constants import (
    DEFAULT_AI_GATEWAY_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_CHROMADB_COLLECTION,
    DEFAULT_CHROMADB_PERSIST_DIR,
)


def setup_logging(
    level: int = logging.INFO,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Set up logging configuration for the application.

    Args:
        level: Logging level (default: INFO)
        log_format: Custom log format string
        log_file: Optional log file path

    Returns:
        Configured logger instance
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create logger
    logger = logging.getLogger("demo_agent")
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_ai_gateway_config(
    logger: logging.Logger,
    issuer_url: Optional[str],
    client_id: Optional[str],
    registration_id: Optional[str],
) -> None:
    """
    Log AI Gateway configuration information.

    Args:
        logger: Logger instance
        issuer_url: AI Gateway issuer URL
        client_id: AI Gateway client ID
        registration_id: AI Gateway registration ID
    """
    logger.info("AI Gateway Configuration:")
    logger.info("  ISSUER_URL: %s", issuer_url or "Not set")
    logger.info("  CLIENT_ID: %s", client_id or "Not set")
    logger.info("  AI_GATEWAY_REGISTRATION_ID: %s", registration_id or "Not set")


def log_ai_gateway_auth(
    logger: logging.Logger,
    access_token: Optional[str],
) -> None:
    """
    Log AI Gateway authentication status.

    Args:
        logger: Logger instance
        access_token: Access token if available
    """
    if access_token:
        logger.info("AI Gateway authentication successful")
        logger.debug("Access token: %s...", access_token[:20])
    else:
        logger.error(ERROR_AI_GATEWAY_TOKEN)
        logger.error(ERROR_AI_GATEWAY_CONFIG)


def log_agent_initialization(
    logger: logging.Logger,
    success: bool,
    error: Optional[Exception] = None,
) -> None:
    """
    Log agent initialization status.

    Args:
        logger: Logger instance
        success: Whether initialization was successful
        error: Exception if initialization failed
    """
    if success:
        logger.info("John Deere agent initialized successfully")
    else:
        logger.error(ERROR_AGENT_INITIALIZATION.format(error))


def log_query_processing(
    logger: logging.Logger,
    success: bool,
    error: Optional[Exception] = None,
) -> None:
    """
    Log query processing status.

    Args:
        logger: Logger instance
        success: Whether query processing was successful
        error: Exception if processing failed
    """
    if success:
        logger.debug("Query processed successfully")
    else:
        logger.error(ERROR_QUERY_PROCESSING.format(error))


# Default logger instance
logger = setup_logging()

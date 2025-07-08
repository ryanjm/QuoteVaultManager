"""
Logging utilities for quote_vault_manager.
Provides setup and action/error logging with clean, reusable patterns.
"""
import logging
import os
from typing import Dict, Any, Tuple
from datetime import datetime

# Type alias for config dict
type ConfigDict = Dict[str, str]

# Logger name constants
_STD_LOGGER_NAME = 'quote_vault_manager.std'
_ERR_LOGGER_NAME = 'quote_vault_manager.err'


def _create_file_handler(path: str, level: int) -> logging.FileHandler:
    """Create a file handler for logging."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handler = logging.FileHandler(path)
    handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    return handler


def _setup_logger(name: str, log_path: str, level: int) -> logging.Logger:
    """Create and configure a logger with a file handler if log_path is provided."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()
    if log_path:
        logger.addHandler(_create_file_handler(log_path, level))
    return logger


def setup_logging(config: ConfigDict) -> Tuple[logging.Logger, logging.Logger]:
    """
    Set up logging to both stdout and error log files.
    Returns a tuple of (std_logger, err_logger).
    """
    std_log_path = config.get('std_log_path', '')
    err_log_path = config.get('err_log_path', '')

    std_logger = _setup_logger(_STD_LOGGER_NAME, std_log_path, logging.INFO)
    err_logger = _setup_logger(_ERR_LOGGER_NAME, err_log_path, logging.ERROR)
    return std_logger, err_logger


def log_sync_action(
    logger: logging.Logger,
    action: str,
    details: str,
    dry_run: bool = False
) -> None:
    """
    Log a sync action with a dividing line and optional dry-run prefix.
    """
    dt_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    dividing_line = f"==== SYNC ACTION [{dt_str}] ===="
    logger.info(dividing_line)
    prefix = "[DRY-RUN] " if dry_run else ""
    logger.info(f"{prefix}{action}: {details}")


def log_error(
    logger: logging.Logger,
    error: str,
    context: str = ""
) -> None:
    """
    Log an error with optional context.
    """
    if context:
        logger.error(f"{context}: {error}")
    else:
        logger.error(error) 
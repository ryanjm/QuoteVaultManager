import logging
import os
from typing import Dict, Any

def setup_logging(config: Dict[str, str]) -> tuple[logging.Logger, logging.Logger]:
    """
    Sets up logging to both stdout and error log files.
    Returns a tuple of (std_logger, err_logger).
    """
    # Create log directories if they don't exist
    std_log_path = config.get('std_log_path', '')
    err_log_path = config.get('err_log_path', '')
    
    if std_log_path:
        os.makedirs(os.path.dirname(std_log_path), exist_ok=True)
    if err_log_path:
        os.makedirs(os.path.dirname(err_log_path), exist_ok=True)
    
    # Setup standard logger
    std_logger = logging.getLogger('quote_vault_manager.std')
    std_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    std_logger.handlers.clear()
    
    # Add file handler if path is specified
    if std_log_path:
        file_handler = logging.FileHandler(std_log_path)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        std_logger.addHandler(file_handler)
    
    # Setup error logger
    err_logger = logging.getLogger('quote_vault_manager.err')
    err_logger.setLevel(logging.ERROR)
    
    # Clear existing handlers
    err_logger.handlers.clear()
    
    # Add file handler if path is specified
    if err_log_path:
        file_handler = logging.FileHandler(err_log_path)
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        err_logger.addHandler(file_handler)
    
    return std_logger, err_logger

def log_sync_action(logger: logging.Logger, action: str, details: str, dry_run: bool = False):
    """
    Logs a sync action with appropriate dry-run prefix.
    """
    prefix = "[DRY-RUN] " if dry_run else ""
    logger.info(f"{prefix}{action}: {details}")

def log_error(logger: logging.Logger, error: str, context: str = ""):
    """
    Logs an error with optional context.
    """
    if context:
        logger.error(f"{context}: {error}")
    else:
        logger.error(error) 
import logging
import os
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

class Logger:
    _instance = None
    _STD_LOGGER_NAME = 'quote_vault_manager.std'
    _ERR_LOGGER_NAME = 'quote_vault_manager.err'

    def __init__(self, std_log_path: str = '', err_log_path: str = ''):
        self.std_log_path = std_log_path
        self.err_log_path = err_log_path
        self.std_logger: logging.Logger = logging.getLogger(self._STD_LOGGER_NAME)
        self.err_logger: logging.Logger = logging.getLogger(self._ERR_LOGGER_NAME)
        self.setup()

    @classmethod
    def get_instance(cls, std_log_path: str = '', err_log_path: str = ''):
        if cls._instance is None:
            cls._instance = cls(std_log_path, err_log_path)
        return cls._instance

    def _create_file_handler(self, path: str, level: int) -> logging.FileHandler:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        handler = logging.FileHandler(path)
        handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        return handler

    def _setup_logger(self, name: str, log_path: str, level: int) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.handlers.clear()
        if log_path:
            logger.addHandler(self._create_file_handler(log_path, level))
        return logger

    def setup(self):
        self.std_logger = self._setup_logger(self._STD_LOGGER_NAME, self.std_log_path, logging.INFO)
        self.err_logger = self._setup_logger(self._ERR_LOGGER_NAME, self.err_log_path, logging.ERROR)

    def log_sync_action(self, action: str, details: str, dry_run: bool = False) -> None:
        logger = self.std_logger or logging.getLogger(self._STD_LOGGER_NAME)
        dt_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dividing_line = f"==== SYNC ACTION [{dt_str}] ===="
        logger.info(dividing_line)
        prefix = "[DRY-RUN] " if dry_run else ""
        logger.info(f"{prefix}{action}: {details}")

    def log_error(self, error: str, context: str = "") -> None:
        logger = self.err_logger or logging.getLogger(self._ERR_LOGGER_NAME)
        if context:
            logger.error(f"{context}: {error}")
        else:
            logger.error(error) 
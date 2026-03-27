"""
Logging configuration for the trading bot.
Sets up both file and console handlers with structured formatting.
"""

import logging
import os
from datetime import datetime


def setup_logger(name: str = "trading_bot", log_dir: str = "logs") -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.

    Args:
        name: Logger name / log file prefix.
        log_dir: Directory where log files are stored.

    Returns:
        Configured logging.Logger instance.
    """
    os.makedirs(log_dir, exist_ok=True)

    log_filename = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # --- File handler (DEBUG+) ---
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    # --- Console handler (INFO+) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logger initialised — file: %s", log_filename)
    return logger

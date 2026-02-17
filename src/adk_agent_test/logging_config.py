"""Logging configuration for the application."""

import logging
import os
import sys


def setup_logging(log_level: str | None = None) -> None:
    """Configure root logger with level from config or LOG_LEVEL env.

    Use LOG_LEVEL=none (or off/disabled/silent) to suppress all log output.
    """
    level_str = (log_level or os.getenv("LOG_LEVEL", "INFO")).strip()
    level_upper = level_str.upper()
    if level_upper in ("NONE", "OFF", "DISABLED", "SILENT"):
        logging.disable(logging.CRITICAL)
        return
    level = getattr(logging, level_upper, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module name."""
    return logging.getLogger(name)

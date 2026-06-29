"""
Centralised logging configuration for the Diagnostic Engine.

All modules should obtain their logger via:

    from app.utils.logger import get_logger
    logger = get_logger(__name__)
"""

import logging
import sys
from app.config import settings


def configure_logging() -> None:
    """
    Configure the root logger once at application startup.

    Log level and format are driven by environment variables
    (see :class:`app.config.Settings`).
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(log_level)

    # Avoid adding duplicate handlers on reload (uvicorn --reload re-imports)
    if not root.handlers:
        root.addHandler(handler)
    else:
        root.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    """Return a named logger inheriting the root configuration."""
    return logging.getLogger(name)

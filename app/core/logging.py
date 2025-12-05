"""
Structured logging configuration for FastAPI application.

Features:
- JSON format for production (machine-parseable for log aggregators)
- Human-readable console format for development
- Request correlation IDs via contextvars
- Configured via LOG_LEVEL and LOG_FORMAT environment variables
"""

import logging
import sys
from contextvars import ContextVar
from typing import Optional

from app.core.config import settings

# Context variable for request correlation ID
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """Add request_id to log records from context variable."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


def setup_logging() -> None:
    """Configure logging based on settings."""
    
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create formatter based on format setting
    if settings.LOG_FORMAT == "json":
        # JSON format for production - easy to parse by log aggregators
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", '
            '"request_id": "%(request_id)s", "message": "%(message)s"}'
        )
    else:
        # Console format for development - human readable
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | [%(request_id)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Add stream handler with formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())
    root_logger.addHandler(handler)
    
    # Set library log levels (reduce noise from third-party libraries)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.DEBUG else logging.WARNING
    )
    
    # Log startup
    logger = get_logger(__name__)
    logger.info(f"Logging configured: level={settings.LOG_LEVEL}, format={settings.LOG_FORMAT}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)

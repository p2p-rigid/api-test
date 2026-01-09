"""
Logging configuration module using structlog for structured logging.
"""
import structlog
import logging
import sys
from typing import Any, Dict
from app.config.settings import settings


def configure_logging() -> None:
    """
    Configure structlog with appropriate processors and formatters.
    """
    # Configure standard logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.debug else logging.INFO,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not settings.debug else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.AsyncBoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Name of the logger (typically __name__)
        
    Returns:
        Configured structlog logger instance
    """
    return structlog.get_logger(name)


def bind_request_context(correlation_id: str = None, user_id: int = None) -> None:
    """
    Bind request-level context to the logger.
    
    Args:
        correlation_id: Unique identifier for the request
        user_id: ID of the authenticated user (if any)
    """
    ctx = {}
    if correlation_id:
        ctx["correlation_id"] = correlation_id
    if user_id:
        ctx["user_id"] = user_id
        
    if ctx:
        structlog.contextvars.bind_contextvars(**ctx)


def clear_request_context() -> None:
    """
    Clear the current request context.
    """
    structlog.contextvars.clear_contextvars()
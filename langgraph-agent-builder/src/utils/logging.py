"""Logging utilities for LangGraph Agent Builder."""

import logging
import sys
from typing import Optional

# Import with fallback
try:
    import structlog
except ImportError:
    # Fallback structlog implementation
    class structlog:
        @staticmethod
        def configure(**kwargs):
            pass
        
        @staticmethod
        def get_logger(name=None):
            return logging.getLogger(name)
        
        class stdlib:
            @staticmethod
            def filter_by_level(): pass
            @staticmethod
            def add_logger_name(): pass
            @staticmethod
            def add_log_level(): pass
            @staticmethod
            def PositionalArgumentsFormatter(): pass
            
            class LoggerFactory:
                pass
        
        class processors:
            @staticmethod
            def TimeStamper(**kwargs): pass
            @staticmethod
            def StackInfoRenderer(): pass
            @staticmethod
            def format_exc_info(): pass
            @staticmethod
            def UnicodeDecoder(): pass
            @staticmethod
            def JSONRenderer(): pass
        
        class dev:
            @staticmethod
            def ConsoleRenderer(): pass


def setup_logging(
    level: str = "INFO",
    format: str = "json",
    log_file: Optional[str] = None
) -> None:
    """
    Setup structured logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format: Log format (json, console)
        log_file: Optional log file path
    """
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        stream=sys.stdout,
        format="%(message)s" if format == "json" else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str):
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        A structured logger instance
    """
    return structlog.get_logger(name) 
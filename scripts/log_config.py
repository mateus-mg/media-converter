#!/usr/bin/env python3
"""
Centralized logging configuration for Media Converter System
"""

from typing import Optional
import uuid
import logging
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler
from logging.handlers import RotatingFileHandler

console = Console()

# Log symbols
SYMBOLS = {
    'success': '✓',
    'error': '✗',
    'warning': '!',
    'info': '',
    'convert': '',
    'image': '',
    'video': '',
    'progress': '',
    'size': '',
    'quality': '',
    'codec': '',
    'metadata': '',
    'speed': '',
    'hardware': '',
    'software': '',
    'preset': '',
    'resolution': '',
    'format': '',
    'duration': '',
    'aspect': '',
    'optimize': ''
}


class MediaConverterLogger:
    """Centralized logger for Media Converter System"""

    def __init__(self, name: str = "MediaConverter", log_file: str = None):
        self.name = name
        self.logger = logging.getLogger(name)

        # Avoid duplicate handlers
        if self.logger.handlers:
            return

        # Get log level from environment or default to INFO
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Console handler with Rich
        console_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
            markup=False
        )
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(message)s',
            datefmt='[%X]'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # File handler with rotation
        if log_file is None:
            script_path = Path(os.getenv('SCRIPT_PATH', os.getcwd()))
            logs_dir = script_path / 'logs'
            logs_dir.mkdir(exist_ok=True)
            log_file = logs_dir / 'media_converter.log'

        # Use rotating file handler with max size of 10MB and up to 5 backup files
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        """Return the configured logger"""
        return self.logger

    @staticmethod
    def format_message(symbol_key: str, message: str) -> str:
        """Format message with symbol"""
        symbol = SYMBOLS.get(symbol_key, '')
        return f"{symbol} {message}" if symbol else message


# Global request ID for tracking related operations
_current_request_id = None


def set_request_id(request_id: Optional[str] = None):
    """Set a request ID for tracking related operations"""
    global _current_request_id
    _current_request_id = request_id or str(uuid.uuid4())[:8]


def get_request_id() -> Optional[str]:
    """Get the current request ID"""
    return _current_request_id


def clear_request_id():
    """Clear the current request ID"""
    global _current_request_id
    _current_request_id = None


def format_log_message(message: str, include_request_id: bool = True) -> str:
    """Format a log message with optional request ID"""
    if include_request_id and _current_request_id:
        return f"[{_current_request_id}] {message}"
    return message

# Create default logger instance


def get_logger(name: str = "MediaConverter") -> logging.Logger:
    """Get or create a logger instance"""
    return MediaConverterLogger(name).get_logger()


def _emit(
    logger: logging.Logger,
    level: int,
    symbol_key: str,
    message: str,
    include_request_id: bool = True,
):
    """Emit a log preserving the real caller location in formatter fields."""
    formatted_message = format_log_message(message, include_request_id)
    payload = MediaConverterLogger.format_message(
        symbol_key, formatted_message)
    logger.log(level, payload, stacklevel=3)


# Convenience functions for formatted logging
def log_success(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log success message"""
    _emit(logger, logging.INFO, 'success', message, include_request_id)


def log_error(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log error message"""
    _emit(logger, logging.ERROR, 'error', message, include_request_id)


def log_warning(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log warning message"""
    _emit(logger, logging.WARNING, 'warning', message, include_request_id)


def log_info(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log info message"""
    _emit(logger, logging.INFO, 'info', message, include_request_id)


def log_convert(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log conversion operation message"""
    _emit(logger, logging.INFO, 'convert', message, include_request_id)


def log_image(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log image operation message"""
    _emit(logger, logging.INFO, 'image', message, include_request_id)


def log_video(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log video operation message"""
    _emit(logger, logging.INFO, 'video', message, include_request_id)


def log_progress(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log progress operation message"""
    _emit(logger, logging.INFO, 'progress', message, include_request_id)


def log_size(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log size operation message"""
    _emit(logger, logging.INFO, 'size', message, include_request_id)


def log_quality(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log quality operation message"""
    _emit(logger, logging.INFO, 'quality', message, include_request_id)


def log_codec(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log codec operation message"""
    _emit(logger, logging.INFO, 'codec', message, include_request_id)


def log_metadata(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log metadata operation message"""
    _emit(logger, logging.INFO, 'metadata', message, include_request_id)


def log_speed(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log speed operation message"""
    _emit(logger, logging.INFO, 'speed', message, include_request_id)


def log_hardware(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log hardware acceleration operation message"""
    _emit(logger, logging.INFO, 'hardware', message, include_request_id)


def log_software(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log software encoding operation message"""
    _emit(logger, logging.INFO, 'software', message, include_request_id)


def log_preset(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log preset operation message"""
    _emit(logger, logging.INFO, 'preset', message, include_request_id)


def log_resolution(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log resolution operation message"""
    _emit(logger, logging.INFO, 'resolution', message, include_request_id)


def log_format(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log format operation message"""
    _emit(logger, logging.INFO, 'format', message, include_request_id)


def log_duration(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log duration operation message"""
    _emit(logger, logging.INFO, 'duration', message, include_request_id)


def log_aspect(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log aspect ratio operation message"""
    _emit(logger, logging.INFO, 'aspect', message, include_request_id)


def log_optimize(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log optimization operation message"""
    _emit(logger, logging.INFO, 'optimize', message, include_request_id)


def log_debug(logger: logging.Logger, message: str, include_request_id: bool = True):
    """Log debug message"""
    formatted_message = format_log_message(message, include_request_id)
    logger.debug(formatted_message, stacklevel=2)


def is_verbose_logging() -> bool:
    """Check if verbose logging is enabled (DEBUG level)"""
    return os.getenv('LOG_LEVEL', 'INFO').upper() == 'DEBUG'


def set_console_log_level(level: int = logging.WARNING):
    """Set console logging level for all loggers

    Args:
        level: logging level (logging.WARNING, logging.ERROR, etc.)

    Use this to suppress INFO logs from console when running CLI commands.
    File logging will continue to capture all levels.
    """
    # Get all loggers
    for logger_name in logging.root.manager.loggerDict:
        logger_obj = logging.getLogger(logger_name)

        # Find RichHandler (console handler) and update its level
        for handler in logger_obj.handlers:
            if isinstance(handler, RichHandler):
                handler.setLevel(level)

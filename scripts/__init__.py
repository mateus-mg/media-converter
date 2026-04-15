"""
Media Converter Scripts Package

This package contains all the core modules for the Media Converter system:
- media_converter: Main conversion logic
- cli_manager: Rich CLI interface
- config: Configuration management from .env
- interactive_helpers: Shared interactive prompts
- log_config: Logging configuration
- log_formatter: Log formatting utilities
"""

from .config import config, get_config

__all__ = [
    'config',
    'get_config',
]

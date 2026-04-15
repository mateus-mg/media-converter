"""
Configuration module for Media Converter.
Loads settings from .env file with sensible defaults.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

# Try to load python-dotenv if available
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


class Config:
    """
    Configuration manager that loads settings from .env file.
    Falls back to sensible defaults if .env is not present.
    """

    # Default values matching .env.example
    DEFAULTS: Dict[str, Any] = {
        # Conversion defaults
        'IMAGE_FORMAT': 'JPEG',
        'VIDEO_CODEC': 'h264',
        'VIDEO_QUALITY': 'auto',
        'RESIZE': 'none',

        # Performance
        'MAX_WORKERS_IMAGES': 4,
        'MAX_WORKERS_VIDEOS': 2,
        'CPU_THRESHOLD_PERCENT': 80,
        'MEMORY_THRESHOLD_PERCENT': 85,
        'MONITOR_SYSTEM_RESOURCES': True,

        # Cache
        'MAX_CACHE_SIZE': 1000,
        'CACHE_EXPIRE_MINUTES': 60,

        # Safety
        'MAX_RETRIES': 3,
        'DISK_SPACE_SAFETY_FACTOR': 1.5,
        'TEMP_CLEANUP_ENABLED': True,

        # Custom parameters
        'CUSTOM_FFMPEG_PARAMS': {},
        'CUSTOM_IMAGE_PARAMS': {},

        # Logging
        'LOG_LEVEL': 'INFO',
        'LOG_TO_FILE': True,
        'LOG_FILE': 'logs/media_converter.log',

        # Conversion database
        'CONVERSION_DB_FILE': 'data/conversion_db.json',
    }

    _instance: Optional['Config'] = None
    _loaded: bool = False

    def __new__(cls) -> 'Config':
        """Singleton pattern to ensure only one config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize and load configuration."""
        if not Config._loaded:
            self._config: Dict[str, Any] = {}
            self._load_config()
            Config._loaded = True

    def _find_project_root(self) -> Path:
        """Find project root by looking for .env or .env.example."""
        current = Path(__file__).resolve().parent

        # Go up directories looking for project markers
        for _ in range(5):
            if (current / '.env').exists() or (current / '.env.example').exists():
                return current
            if (current / 'media-converter').exists():
                return current
            parent = current.parent
            if parent == current:
                break
            current = parent

        # Fallback to scripts parent directory
        return Path(__file__).resolve().parent.parent

    def _load_config(self) -> None:
        """Load configuration from .env file."""
        project_root = self._find_project_root()
        env_file = project_root / '.env'

        # Load .env file if python-dotenv is available
        if HAS_DOTENV and env_file.exists():
            load_dotenv(env_file)

        # Load all settings
        for key, default in self.DEFAULTS.items():
            self._config[key] = self._get_env_value(key, default)

    def _get_env_value(self, key: str, default: Any) -> Any:
        """Get value from environment with proper type conversion."""
        value = os.environ.get(key)

        if value is None:
            return default

        # Type conversion based on default type
        if isinstance(default, bool):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(default, int):
            try:
                return int(value)
            except ValueError:
                return default
        elif isinstance(default, float):
            try:
                return float(value)
            except ValueError:
                return default
        elif isinstance(default, dict):
            try:
                return json.loads(value) if value else default
            except json.JSONDecodeError:
                return default
        else:
            return value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access to configuration."""
        if name.startswith('_') or name in ('DEFAULTS', 'get'):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'")

        upper_name = name.upper()
        if upper_name in self._config:
            return self._config[upper_name]
        raise AttributeError(f"Configuration key '{name}' not found")

    def reload(self) -> None:
        """Reload configuration from .env file."""
        Config._loaded = False
        self._load_config()
        Config._loaded = True

    def to_dict(self) -> Dict[str, Any]:
        """Return all configuration as a dictionary."""
        return self._config.copy()

    @property
    def image_format(self) -> str:
        return self._config['IMAGE_FORMAT']

    @property
    def video_codec(self) -> str:
        return self._config['VIDEO_CODEC']

    @property
    def video_quality(self) -> str:
        return self._config['VIDEO_QUALITY']

    @property
    def resize(self) -> str:
        return self._config['RESIZE']

    @property
    def max_workers_images(self) -> int:
        return self._config['MAX_WORKERS_IMAGES']

    @property
    def max_workers_videos(self) -> int:
        return self._config['MAX_WORKERS_VIDEOS']

    @property
    def cpu_threshold(self) -> int:
        return self._config['CPU_THRESHOLD_PERCENT']

    @property
    def memory_threshold(self) -> int:
        return self._config['MEMORY_THRESHOLD_PERCENT']

    @property
    def monitor_resources(self) -> bool:
        return self._config['MONITOR_SYSTEM_RESOURCES']

    @property
    def max_cache_size(self) -> int:
        return self._config['MAX_CACHE_SIZE']

    @property
    def cache_expire_minutes(self) -> int:
        return self._config['CACHE_EXPIRE_MINUTES']

    @property
    def max_retries(self) -> int:
        return self._config['MAX_RETRIES']

    @property
    def disk_space_safety_factor(self) -> float:
        return self._config['DISK_SPACE_SAFETY_FACTOR']

    @property
    def temp_cleanup(self) -> bool:
        return self._config['TEMP_CLEANUP_ENABLED']

    @property
    def custom_ffmpeg_params(self) -> Dict:
        return self._config['CUSTOM_FFMPEG_PARAMS']

    @property
    def custom_image_params(self) -> Dict:
        return self._config['CUSTOM_IMAGE_PARAMS']

    @property
    def log_level(self) -> str:
        return self._config['LOG_LEVEL']

    @property
    def log_to_file(self) -> bool:
        return self._config['LOG_TO_FILE']

    @property
    def log_file(self) -> str:
        return self._config['LOG_FILE']

    @property
    def conversion_db_file(self) -> str:
        return self._config['CONVERSION_DB_FILE']


# Singleton instance for easy import
config = Config()


def get_config() -> Config:
    """Get the configuration singleton instance."""
    return config

"""Configuration loading functionality for Captain's Log."""

from pathlib import Path

import yaml

from .config_models import Config


class ConfigLoader:
    """Handles loading and caching of Captain's Log configuration."""

    DEFAULT_CONFIG_PATH = Path.home() / ".captains-log" / "config.yml"

    def __init__(self, config_path: Path = None):
        """Initialize with optional custom config path."""
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._cached_config = None

    def load_config(self, force_reload: bool = False) -> Config:
        """Load configuration from file, with caching."""
        if self._cached_config is not None and not force_reload:
            return self._cached_config

        try:
            if self.config_path.exists():
                with open(self.config_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            else:
                data = {}
        except (OSError, yaml.YAMLError) as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            data = {}

        self._cached_config = Config.from_dict(data)
        return self._cached_config

    def clear_cache(self):
        """Clear the cached configuration."""
        self._cached_config = None


# Global default instance
_default_loader = ConfigLoader()


def load_config(force_reload: bool = False) -> Config:
    """Load configuration using the default loader."""
    return _default_loader.load_config(force_reload)


def set_config_path(config_path: Path):
    """Set a custom config path for the default loader."""
    global _default_loader
    _default_loader = ConfigLoader(config_path)

"""Tests for the config module."""

from pathlib import Path
from unittest.mock import patch

import yaml

from src.config import Config, ConfigLoader, ProjectConfig


# ProjectConfig tests
def test_project_config_from_dict_string_format():
    """Test creating ProjectConfig from string."""
    config = ProjectConfig.from_dict("/tmp/test")
    assert config.root == Path("/tmp/test").resolve()
    assert config.log_repo is None


def test_project_config_from_dict_dict_format():
    """Test creating ProjectConfig from dictionary."""
    data = {"root": "/tmp/test", "log_repo": "/tmp/logs"}
    config = ProjectConfig.from_dict(data)
    assert config.root == Path("/tmp/test").resolve()
    assert config.log_repo == Path("/tmp/logs").resolve()


def test_project_config_from_dict_empty():
    """Test creating ProjectConfig from None or empty."""
    config = ProjectConfig.from_dict(None)
    assert config.root is None
    assert config.log_repo is None


# Config tests
def test_config_from_dict_complete():
    """Test creating Config from complete dictionary."""
    data = {
        "global_log_repo": "/tmp/global",
        "projects": {
            "test1": "/tmp/test1",
            "test2": {"root": "/tmp/test2", "log_repo": "/tmp/test2-logs"},
        },
    }
    config = Config.from_dict(data)

    assert config.global_log_repo == Path("/tmp/global").resolve()
    assert len(config.projects) == 2
    assert config.projects["test1"].root == Path("/tmp/test1").resolve()
    assert config.projects["test2"].log_repo == Path("/tmp/test2-logs").resolve()


def test_config_from_dict_empty():
    """Test creating Config from empty dictionary."""
    config = Config.from_dict({})
    assert config.global_log_repo is None
    assert config.projects == {}


def test_config_get_project_config():
    """Test getting project configuration."""
    data = {"projects": {"test": "/tmp/test"}}
    config = Config.from_dict(data)

    # Existing project
    project_config = config.get_project_config("test")
    assert project_config.root == Path("/tmp/test").resolve()

    # Non-existing project
    default_config = config.get_project_config("nonexistent")
    assert default_config.root is None


# ConfigLoader tests
def test_config_loader_load_config_file_exists(tmp_path):
    """Test loading config from existing file."""
    config_data = {"global_log_repo": "/tmp/logs", "projects": {"test": "/tmp/test"}}
    config_file = tmp_path / "config.yml"

    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    loader = ConfigLoader(config_file)
    config = loader.load_config()

    assert config.global_log_repo == Path("/tmp/logs").resolve()
    assert "test" in config.projects


def test_config_loader_load_config_file_not_exists(tmp_path):
    """Test loading config when file doesn't exist."""
    config_file = tmp_path / "nonexistent.yml"
    loader = ConfigLoader(config_file)
    config = loader.load_config()

    assert config.global_log_repo is None
    assert config.projects == {}


def test_config_loader_load_config_caching(tmp_path):
    """Test that config is cached properly."""
    config_file = tmp_path / "config.yml"
    config_file.write_text("global_log_repo: /tmp/logs")

    loader = ConfigLoader(config_file)

    # First load
    config1 = loader.load_config()

    # Second load should return cached version
    config2 = loader.load_config()
    assert config1 is config2

    # Force reload should create new instance
    config3 = loader.load_config(force_reload=True)
    assert config1 is not config3


def test_config_loader_clear_cache(tmp_path):
    """Test clearing cache."""
    config_file = tmp_path / "config.yml"
    config_file.write_text("global_log_repo: /tmp/logs")

    loader = ConfigLoader(config_file)
    config1 = loader.load_config()

    loader.clear_cache()
    config2 = loader.load_config()

    assert config1 is not config2


def test_config_loader_load_config_yaml_error(tmp_path):
    """Test handling of YAML parsing errors."""
    config_file = tmp_path / "config.yml"
    config_file.write_text("invalid: yaml: content: [")

    loader = ConfigLoader(config_file)
    with patch("builtins.print") as mock_print:
        config = loader.load_config()
        mock_print.assert_called()

    assert config.global_log_repo is None

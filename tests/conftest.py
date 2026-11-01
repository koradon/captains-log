"""Keep CLI/configuration and Git tests away from the developer's home."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.config import config_loader
from src.logs import LogManager


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    home = tmp_path / "isolated-home"
    home.mkdir()
    for key in list(os.environ):
        if key.startswith(("GIT_", "CAPTAINS_LOG_")):
            monkeypatch.delenv(key)
    for key, value in {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.hooksPath",
        "GIT_CONFIG_VALUE_0": "/dev/null",
        "GIT_ALLOW_PROTOCOL": "file",
    }.items():
        monkeypatch.setenv(key, value)
    config_path = home / ".captains-log" / "config.yml"
    (home / ".gitconfig").write_text("[core]\n\thooksPath = /dev/null\n")
    monkeypatch.setattr(config_loader.ConfigLoader, "DEFAULT_CONFIG_PATH", config_path)
    monkeypatch.setattr(
        config_loader, "_default_loader", config_loader.ConfigLoader(config_path)
    )
    monkeypatch.setattr(LogManager, "BASE_DIR", home / ".captains-log" / "projects")
    for name in ("update_log", "src.update_log"):
        if name in sys.modules:
            monkeypatch.setattr(sys.modules[name], "BASE_DIR", LogManager.BASE_DIR)


def disable_git_hooks(repo: Path) -> None:
    """Prevent temporary test repositories from invoking the machine's global hooks."""
    subprocess.run(
        ["git", "-C", str(repo), "config", "core.hooksPath", "/dev/null"],
        check=True,
        capture_output=True,
        timeout=20,
    )

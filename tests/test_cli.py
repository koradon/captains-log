"""Tests for the captains-log CLI."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from src import cli


def test_print_version(capsys):
    """print_version prints version string."""
    cli.print_version()
    out = capsys.readouterr().out
    assert "Captain's Log v" in out


def test_main_no_args_shows_usage_and_exits(monkeypatch, capsys):
    """main with no args prints usage and exits with 0."""
    monkeypatch.setattr(cli.sys, "argv", ["captains-log"])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    out = capsys.readouterr().out
    assert "Captain's Log" in out
    assert "Usage:" in out
    assert exc.value.code == 0


def test_main_version_flag_calls_print_version(monkeypatch, capsys):
    """main --version prints version."""
    monkeypatch.setattr(cli.sys, "argv", ["captains-log", "--version"])

    cli.main()

    out = capsys.readouterr().out
    assert "Captain's Log v" in out


def test_main_version_short_flag(monkeypatch, capsys):
    """main -v prints version."""
    monkeypatch.setattr(cli.sys, "argv", ["captains-log", "-v"])

    cli.main()

    out = capsys.readouterr().out
    assert "Captain's Log v" in out


def test_main_unknown_command_exits_with_error(monkeypatch, capsys):
    """main with unknown command prints error and exits with 1."""
    monkeypatch.setattr(cli.sys, "argv", ["captains-log", "unknown-cmd"])

    with pytest.raises(SystemExit) as exc:
        cli.main()

    out = capsys.readouterr().out
    assert "Unknown command" in out
    assert "unknown-cmd" in out
    assert exc.value.code == 1


def test_main_setup_runs_setup(monkeypatch, capsys, tmp_path):
    """main setup runs setup() and creates directories."""
    monkeypatch.setattr(cli.sys, "argv", ["captains-log", "setup"])
    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)

    # Mock subprocess to avoid touching git config
    mock_run = MagicMock()
    mock_run.return_value.stdout = str(tmp_path / ".git-hooks")
    monkeypatch.setattr(cli.subprocess, "run", mock_run)

    cli.main()

    out = capsys.readouterr().out
    assert "=== Captain's Log Setup ===" in out
    assert (tmp_path / ".captains-log").exists()
    assert (tmp_path / ".git-hooks").exists()


def test_main_setup_runs_with_log_level_flag(monkeypatch, capsys, tmp_path):
    """main supports global --log-level before command."""
    monkeypatch.setattr(
        cli.sys, "argv", ["captains-log", "--log-level", "debug", "setup"]
    )
    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)

    mock_run = MagicMock()
    mock_run.return_value.stdout = str(tmp_path / ".git-hooks")
    monkeypatch.setattr(cli.subprocess, "run", mock_run)

    cli.main()

    out = capsys.readouterr().out
    assert "=== Captain's Log Setup ===" in out


def test_main_rejects_invalid_log_level(monkeypatch, capsys):
    """main exits with code 1 for unsupported --log-level."""
    monkeypatch.setattr(
        cli.sys, "argv", ["captains-log", "--log-level", "trace", "setup"]
    )

    with pytest.raises(SystemExit) as exc:
        cli.main()

    out = capsys.readouterr().out
    assert "invalid --log-level value" in out
    assert exc.value.code == 1


def test_setup_package_not_found_exits(monkeypatch, capsys, tmp_path):
    """setup exits when src has no __file__ (lines 40-43)."""
    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)
    (tmp_path / ".captains-log").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".git-hooks").mkdir(parents=True, exist_ok=True)

    # Replace src with object that has no __file__ to trigger AttributeError

    fake_src = object()  # no __file__ attribute
    with patch.dict(sys.modules, {"src": fake_src}):
        with pytest.raises(SystemExit) as exc:
            cli.setup()

    out = capsys.readouterr().out
    assert "Captain's Log package not found" in out or "ERROR" in out
    assert exc.value.code == 1


def test_setup_subprocess_error_exits(monkeypatch, capsys, tmp_path):
    """setup exits when git config fails (lines 115-117)."""
    import subprocess

    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)
    (tmp_path / ".captains-log").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".git-hooks").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        cli.subprocess,
        "run",
        MagicMock(side_effect=subprocess.CalledProcessError(1, "git")),
    )

    with pytest.raises(SystemExit) as exc:
        cli.setup()

    assert exc.value.code == 1


def test_install_precommit_hooks_creates_hooks(monkeypatch, tmp_path, capsys):
    """install_precommit_hooks creates hook files and configures git."""
    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        cli.subprocess, "run", MagicMock(return_value=MagicMock(stdout=""))
    )

    cli.install_precommit_hooks()

    out = capsys.readouterr().out
    assert "pre-commit wrapper hooks" in out
    assert (tmp_path / ".git-hooks" / "pre-commit").exists()
    assert (tmp_path / ".git-hooks" / "commit-msg").exists()


def test_install_precommit_hooks_subprocess_error_exits(monkeypatch, tmp_path):
    """install_precommit_hooks exits when git config fails (lines 231-233)."""
    import subprocess

    monkeypatch.setattr(cli.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        MagicMock(side_effect=subprocess.CalledProcessError(1, "git config")),
    )

    with pytest.raises(SystemExit) as exc:
        cli.install_precommit_hooks()

    assert exc.value.code == 1

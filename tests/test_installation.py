"""Tests for installation and setup functionality."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.cli import setup


@pytest.fixture
def mock_home(tmp_path):
    """Create a temporary home directory for testing."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    return home_dir


@pytest.fixture
def mock_git_config(tmp_path):
    """Create a temporary git config directory."""
    git_config_dir = tmp_path / "git_config"
    git_config_dir.mkdir()
    return git_config_dir


@pytest.fixture
def mock_src_module(tmp_path):
    """Create a mock src module for testing."""
    package_root = tmp_path / "package"
    package_root.mkdir()
    src_dir = package_root / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")

    mock_src = MagicMock()
    mock_src.__file__ = str(src_dir / "__init__.py")
    return mock_src, package_root


def test_setup_creates_directories(mock_home, mock_git_config, mock_src_module):
    """Test that setup creates ~/.captains-log and ~/.git-hooks directories."""
    mock_src, _ = mock_src_module
    with patch("pathlib.Path.home", return_value=mock_home), patch(
        "subprocess.run"
    ) as mock_subprocess, patch.dict(sys.modules, {"src": mock_src}):
        # Mock git config commands
        mock_subprocess.return_value = MagicMock(stdout="", returncode=0, check=False)

        # Run setup
        setup()

        # Verify directories were created
        capt_log_dir = mock_home / ".captains-log"
        git_hooks_dir = mock_home / ".git-hooks"

        assert capt_log_dir.exists(), "~/.captains-log directory should be created"
        assert capt_log_dir.is_dir(), "~/.captains-log should be a directory"
        assert git_hooks_dir.exists(), "~/.git-hooks directory should be created"
        assert git_hooks_dir.is_dir(), "~/.git-hooks should be a directory"


def test_setup_creates_config_file(mock_home, mock_git_config, mock_src_module):
    """Test that setup creates config.yml in ~/.captains-log."""
    mock_src, _ = mock_src_module
    with patch("pathlib.Path.home", return_value=mock_home), patch(
        "subprocess.run"
    ) as mock_subprocess, patch.dict(sys.modules, {"src": mock_src}):
        mock_subprocess.return_value = MagicMock(stdout="", returncode=0, check=False)

        setup()

        config_file = mock_home / ".captains-log" / "config.yml"
        assert config_file.exists(), "config.yml should be created"
        assert config_file.is_file(), "config.yml should be a file"

        # Verify config file has expected content
        content = config_file.read_text()
        assert "global_log_repo" in content, "Config should contain global_log_repo"
        assert "projects:" in content, "Config should contain projects section"


def test_setup_does_not_overwrite_existing_config(
    mock_home, mock_git_config, mock_src_module
):
    """Test that setup doesn't overwrite existing config.yml."""
    mock_src, _ = mock_src_module
    with patch("pathlib.Path.home", return_value=mock_home), patch(
        "subprocess.run"
    ) as mock_subprocess, patch.dict(sys.modules, {"src": mock_src}):
        mock_subprocess.return_value = MagicMock(stdout="", returncode=0, check=False)

        # Create existing config with custom content
        capt_log_dir = mock_home / ".captains-log"
        capt_log_dir.mkdir()
        config_file = capt_log_dir / "config.yml"
        original_content = (
            "global_log_repo: /custom/path\nprojects:\n  custom: /custom/project"
        )
        config_file.write_text(original_content)

        setup()

        # Verify original content is preserved
        assert config_file.read_text() == original_content, (
            "Existing config should not be overwritten"
        )


def test_setup_installs_commit_msg_hook(mock_home, mock_src_module):
    """Test that setup copies commit-msg hook to ~/.git-hooks."""
    mock_src, package_root = mock_src_module

    # Create commit-msg-package hook
    commit_msg_source = package_root / "commit-msg-package"
    commit_msg_source.write_text("#!/bin/bash\necho 'test hook'")

    with patch("pathlib.Path.home", return_value=mock_home), patch(
        "subprocess.run"
    ) as mock_subprocess, patch.dict(sys.modules, {"src": mock_src}):
        mock_subprocess.return_value = MagicMock(stdout="", returncode=0, check=False)

        setup()

        # Verify hook was copied
        git_hooks_dir = mock_home / ".git-hooks"
        commit_msg_dest = git_hooks_dir / "commit-msg"
        assert commit_msg_dest.exists(), "commit-msg hook should be installed"
        assert commit_msg_dest.is_file(), "commit-msg should be a file"
        assert os.access(commit_msg_dest, os.X_OK), "commit-msg should be executable"
        # Verify hook content was copied
        assert commit_msg_dest.read_text() == commit_msg_source.read_text()


def test_setup_sets_git_hooks_path(mock_home, mock_git_config, mock_src_module):
    """Test that setup sets git config core.hooksPath."""
    mock_src, _ = mock_src_module
    with patch("pathlib.Path.home", return_value=mock_home), patch(
        "subprocess.run"
    ) as mock_subprocess, patch.dict(sys.modules, {"src": mock_src}):
        git_hooks_dir = mock_home / ".git-hooks"

        # First call: get current hooks path (returns empty)
        # Second call: set hooks path
        call_count = 0

        def mock_run_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: git config --global core.hooksPath (get)
                return MagicMock(stdout="", returncode=0, check=False)
            elif call_count == 2:
                # Second call: git config --global core.hooksPath <path> (set)
                assert args[0][-1] == str(git_hooks_dir), (
                    "Should set hooks path to ~/.git-hooks"
                )
                return MagicMock(returncode=0, check=True)
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = mock_run_side_effect

        setup()

        # Verify git config was called to set hooks path
        assert call_count >= 2, "Should call git config at least twice"


def test_setup_does_not_change_existing_git_hooks_path(
    mock_home, mock_git_config, mock_src_module
):
    """Test that setup doesn't change git hooks path if already set correctly."""
    mock_src, _ = mock_src_module
    with patch("pathlib.Path.home", return_value=mock_home), patch(
        "subprocess.run"
    ) as mock_subprocess, patch.dict(sys.modules, {"src": mock_src}):
        git_hooks_dir = mock_home / ".git-hooks"

        call_count = 0

        def mock_run_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: git config --global core.hooksPath (get) - returns current path
                return MagicMock(
                    stdout=str(git_hooks_dir) + "\n", returncode=0, check=False
                )
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = mock_run_side_effect

        setup()

        # Verify git config was called but not to set (since it's already correct)
        assert call_count >= 1, "Should check git config"
        # Should not have called git config to set (only to get)
        set_calls = [
            call
            for call in mock_subprocess.call_args_list
            if len(call[0][0]) > 3 and call[0][0][2] == "core.hooksPath"
        ]
        assert len(set_calls) == 0, "Should not set hooks path if already correct"


def test_setup_handles_missing_commit_msg_hook_gracefully(mock_home, mock_src_module):
    """Test that setup handles missing commit-msg hook gracefully."""
    mock_src, package_root = mock_src_module
    # Don't create commit-msg-package or commit-msg files

    with patch("pathlib.Path.home", return_value=mock_home), patch(
        "subprocess.run"
    ) as mock_subprocess, patch("builtins.print") as mock_print, patch.dict(
        sys.modules, {"src": mock_src}
    ):
        mock_subprocess.return_value = MagicMock(stdout="", returncode=0, check=False)

        # Mock Path.exists() to return False for commit-msg files
        # This ensures all the fallback paths in setup() fail to find the hook
        original_exists = Path.exists

        def mock_exists(self):
            # If this path's name is commit-msg or commit-msg-package, return False
            try:
                name = self.name
                if name in ("commit-msg", "commit-msg-package"):
                    return False
            except (AttributeError, TypeError):
                pass
            # Otherwise use the real exists() method
            return original_exists(self)

        with patch.object(Path, "exists", mock_exists):
            # Setup should complete but warn about missing hook
            setup()

        # Verify warning message was printed
        # Check the actual arguments passed to print
        print_messages = []
        for call in mock_print.call_args_list:
            # call[0] contains positional args as a tuple
            if call[0]:
                # Join all positional args (print can have multiple)
                msg = " ".join(str(arg) for arg in call[0])
                print_messages.append(msg)

        all_printed = " ".join(print_messages).lower()
        assert "warning" in all_printed and "not found" in all_printed, (
            f"Should print warning message when hook not found. Got messages: {print_messages}"
        )


def test_setup_idempotent(mock_home, mock_git_config, mock_src_module):
    """Test that running setup multiple times is idempotent."""
    mock_src, _ = mock_src_module
    with patch("pathlib.Path.home", return_value=mock_home), patch(
        "subprocess.run"
    ) as mock_subprocess, patch.dict(sys.modules, {"src": mock_src}):
        mock_subprocess.return_value = MagicMock(stdout="", returncode=0, check=False)

        # Run setup twice
        setup()
        first_config_content = (mock_home / ".captains-log" / "config.yml").read_text()

        setup()
        second_config_content = (mock_home / ".captains-log" / "config.yml").read_text()

        # Verify config content is the same (or preserved if existed)
        assert first_config_content == second_config_content, (
            "Setup should be idempotent"
        )

        # Verify directories still exist
        assert (mock_home / ".captains-log").exists()
        assert (mock_home / ".git-hooks").exists()


@pytest.mark.integration
def test_pipx_installation_integration(tmp_path):
    """Integration test: Simulate pipx installation and verify setup works."""
    # This test simulates what happens when installed via pipx
    # It doesn't actually install via pipx, but tests the setup command
    # in a way that mimics the pipx installation scenario

    # Create a temporary home directory
    test_home = tmp_path / "test_home"
    test_home.mkdir()

    # Create a fake package structure
    package_root = tmp_path / "package"
    package_root.mkdir()
    src_dir = package_root / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")

    # Create commit-msg-package hook (similar to actual commit-msg-package file)
    commit_msg_hook = package_root / "commit-msg-package"
    commit_msg_hook.write_text("""#!/bin/bash

# Exit on any error
set -e

# Get repository information
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
REPO_PATH=$(git rev-parse --show-toplevel)
COMMIT_MSG=$(head -n1 "$1")

# Get commit SHA (handle both pre-commit and post-commit scenarios)
COMMIT_SHA=$(git rev-parse --verify HEAD 2>/dev/null || echo "no-sha")

# Run the update script using the installed package
export GIT_HOOK=1
if ! python3 -m src.update_log "$REPO_NAME" "$REPO_PATH" "$COMMIT_SHA" "$COMMIT_MSG"; then
    echo "Warning: Captain's Log update failed, but commit will continue"
    echo "Check the script output above for errors"
    exit 0  # Don't fail the commit
fi
""")

    with patch("pathlib.Path.home", return_value=test_home), patch(
        "subprocess.run"
    ) as mock_subprocess:
        # Mock git config
        def mock_git_config(*args, **kwargs):
            if args[0][:3] == ["git", "config", "--global"]:
                if len(args[0]) == 3:
                    # Getting config
                    return MagicMock(stdout="", returncode=0, check=False)
                else:
                    # Setting config
                    return MagicMock(returncode=0, check=True)
            return MagicMock(returncode=0)

        mock_subprocess.side_effect = mock_git_config

        # Mock the src module import
        mock_src = MagicMock()
        mock_src.__file__ = str(src_dir / "__init__.py")
        with patch.dict(sys.modules, {"src": mock_src}):
            setup()

    # Verify all expected files and directories exist
    capt_log_dir = test_home / ".captains-log"
    git_hooks_dir = test_home / ".git-hooks"
    config_file = capt_log_dir / "config.yml"
    commit_msg_hook_installed = git_hooks_dir / "commit-msg"

    assert capt_log_dir.exists(), "~/.captains-log should exist"
    assert git_hooks_dir.exists(), "~/.git-hooks should exist"
    assert config_file.exists(), "config.yml should exist"
    assert commit_msg_hook_installed.exists(), "commit-msg hook should be installed"
    assert os.access(commit_msg_hook_installed, os.X_OK), (
        "commit-msg hook should be executable"
    )

    # Verify hook content - should contain src.update_log (the actual hook uses this)
    hook_content = commit_msg_hook_installed.read_text()
    assert "src.update_log" in hook_content, (
        f"Hook should contain src.update_log. Got: {hook_content[:100]}"
    )

    # Verify config file structure
    config_content = config_file.read_text()
    assert "global_log_repo" in config_content
    assert "projects:" in config_content

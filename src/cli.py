#!/usr/bin/env python3
"""
Captain's Log CLI - Main command-line interface

Provides setup and configuration commands for Captain's Log.
"""

import subprocess
import sys
from pathlib import Path

from . import __version__, cli_logging


def _render_commit_msg_hook(python_executable: str) -> str:
    """Render commit-msg hook content using a specific Python interpreter.

    This avoids relying on `python3` from PATH (which may not have the
    package installed, e.g. when `git-captains-log` is installed via pipx).
    """
    # Use bash for compatibility with existing hook and common shells.
    py = python_executable.replace('"', '\\"')
    return f"""#!/bin/bash

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
if ! "{py}" -m src.update_log "$REPO_NAME" "$REPO_PATH" "$COMMIT_SHA" "$COMMIT_MSG"; then
    echo "Warning: Captain's Log update failed, but commit will continue"
    echo "Check the script output above for errors"
    exit 0  # Don't fail the commit
fi
"""


def print_version():
    """Print the version information."""
    print(f"Captain's Log v{__version__}")


def setup():
    """Set up Captain's Log for the first time."""
    print("=== Captain's Log Setup ===")
    print(f"Version: {__version__}\n")

    capt_log_dir = Path.home() / ".captains-log"
    git_hooks_dir = Path.home() / ".git-hooks"
    config_file = capt_log_dir / "config.yml"

    # Create directories
    print("Creating directories...")
    capt_log_dir.mkdir(parents=True, exist_ok=True)
    git_hooks_dir.mkdir(parents=True, exist_ok=True)

    # Find the installed package location
    try:
        import src

        package_dir = Path(src.__file__).parent
    except (ImportError, AttributeError):
        print("ERROR: Captain's Log package not found. Please install it first:")
        print("  pip install git-captains-log")
        sys.exit(1)

    # Install commit-msg hook
    print("Installing Git commit-msg hook...")

    # Look for commit-msg-package (for package installations) first
    commit_msg_source = package_dir.parent / "commit-msg-package"
    if not commit_msg_source.exists():
        # Fall back to regular commit-msg (for installation script)
        commit_msg_source = package_dir.parent / "commit-msg"
    if not commit_msg_source.exists():
        # Try alternate location (when installed from wheel)
        commit_msg_source = Path(__file__).parent.parent / "commit-msg-package"
    if not commit_msg_source.exists():
        # Final fallback
        commit_msg_source = Path(__file__).parent.parent / "commit-msg"

    commit_msg_dest = git_hooks_dir / "commit-msg"
    if commit_msg_source.exists():
        # Even if we have a hook template file, prefer generating a hook that
        # uses the current interpreter. This matters for pipx installs where
        # `python3` from PATH may not have `git-captains-log` installed.
        hook_content = _render_commit_msg_hook(sys.executable)
        commit_msg_dest.write_text(hook_content, encoding="utf-8")
        commit_msg_dest.chmod(0o755)
        print(f"  ✓ Installed commit-msg hook to {commit_msg_dest}")
    else:
        print("  ⚠ Warning: commit-msg hook not found in package")
        print("    You may need to copy it manually from the repository")

    # Create default config if it doesn't exist
    if not config_file.exists():
        print(f"\nCreating default config at {config_file}...")
        config_content = """# Captain's Log Configuration
#
# This is where your daily logs will be stored
global_log_repo: /path/to/your/log-repo

# Define your projects here
projects:
  example-project:
    root: /path/to/your/repos/example-project
    # Optional: override log location for this project
    # log_repo: /path/to/specific/log-repo

# You can add more projects like this:
#  another-project:
#    root: /path/to/repos/another-project
"""
        config_file.write_text(config_content)
        print("  ✓ Created config file")
        print(f"\n⚠ IMPORTANT: Edit {config_file}")
        print("  Update 'global_log_repo' and add your project paths")
    else:
        print(f"\n✓ Config file already exists at {config_file}")

    # Set global git hooks path
    print("\nConfiguring Git hooks...")
    try:
        current_hooks_path = subprocess.run(
            ["git", "config", "--global", "core.hooksPath"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()

        if current_hooks_path != str(git_hooks_dir):
            subprocess.run(
                ["git", "config", "--global", "core.hooksPath", str(git_hooks_dir)],
                check=True,
            )
            print(f"  ✓ Set global Git hooks path to {git_hooks_dir}")
            if current_hooks_path:
                print(f"  ⚠ Previous hooks path was: {current_hooks_path}")
        else:
            print("  ✓ Git hooks path already configured")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error configuring Git hooks: {e}")
        sys.exit(1)

    # Check if commands are accessible
    print("\n=== Installation Complete! ===\n")
    print("Available commands:")
    print("  btw 'your note'              - Add manual log entries")
    print("  wtf 'what broke'             - Add entries to 'What Broke' section")
    print("  wnext 'what next'            - Add entries to 'Whats next' section")
    print("  stone 'milestone'            - Add entries to yearly milestones file")
    print("  captains-log --version       - Show version")
    print("  captains-log setup           - Run setup again")
    print()
    print("Next steps:")
    print(f"  1. Edit your config: {config_file}")
    print("  2. Set up your log repository")
    print("  3. Start committing! Your commits will be logged automatically")
    print()


def install_precommit_hooks():
    """Install global pre-commit wrapper hooks for Captain's Log."""
    print("=== Installing pre-commit wrapper hooks (global) ===")

    git_hooks_dir = Path.home() / ".git-hooks"
    git_hooks_dir.mkdir(parents=True, exist_ok=True)

    def write_hook(name: str, content: str) -> None:
        path = git_hooks_dir / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)
        print(f"  ✓ Installed {name} to {path}")

    pre_commit = """#!/usr/bin/env sh

# Run repo's pre-commit hooks via pre-commit when configured.
if command -v pre-commit >/dev/null 2>&1 && [ -f ".pre-commit-config.yaml" ]; then
  exec pre-commit run --hook-stage pre-commit --color always
fi

exit 0
"""

    commit_msg_precommit = """#!/usr/bin/env sh

# 1) Run commit-msg stage through pre-commit when configured in this repo
if command -v pre-commit >/dev/null 2>&1 && [ -f ".pre-commit-config.yaml" ]; then
  pre-commit run --hook-stage commit-msg --commit-msg-filename "$1" --color always || exit $?
fi

exit 0
"""

    python_executable = sys.executable.replace('"', '\\"')

    captains_log = f"""#!/usr/bin/env sh

# Captain's Log commit-msg dispatcher
# Behavior:
# - If commit-msg-precommit exists: run pre-commit first
# - Always run Captain's Log hook afterwards using the current interpreter

set -eu

HOOKS_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PRECOMMIT_WRAPPER="$HOOKS_DIR/commit-msg-precommit"

# 1) Run pre-commit wrapper if present
if [ -x "$PRECOMMIT_WRAPPER" ]; then
  "$PRECOMMIT_WRAPPER" "$@"
fi

# 2) Run Captain's Log update via installed package
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
REPO_PATH=$(git rev-parse --show-toplevel)
COMMIT_MSG=$(head -n1 "$1")
COMMIT_SHA=$(git rev-parse --verify HEAD 2>/dev/null || echo "no-sha")

export GIT_HOOK=1
exec "{python_executable}" -m src.update_log "$REPO_NAME" "$REPO_PATH" "$COMMIT_SHA" "$COMMIT_MSG"

exit 0
"""

    pre_push = """#!/usr/bin/env sh

# Run repo's pre-push hooks via pre-commit when configured.
if command -v pre-commit >/dev/null 2>&1 && [ -f ".pre-commit-config.yaml" ]; then
  exec pre-commit run --hook-stage pre-push --color always
fi

exit 0
"""

    write_hook("pre-commit", pre_commit)
    write_hook("commit-msg-precommit", commit_msg_precommit)
    write_hook("commit-msg", captains_log)
    write_hook("pre-push", pre_push)

    # Set global git hooks path
    print("\nConfiguring global Git hooks path...")
    try:
        result = subprocess.run(
            ["git", "config", "--global", "core.hooksPath"],
            capture_output=True,
            text=True,
            check=False,
        )
        current_hooks_path = result.stdout.strip()

        if current_hooks_path != str(git_hooks_dir):
            subprocess.run(
                ["git", "config", "--global", "core.hooksPath", str(git_hooks_dir)],
                check=True,
            )
            print(f"  ✓ Set global Git hooks path to {git_hooks_dir}")
            if current_hooks_path:
                print(f"  ⚠ Previous hooks path was: {current_hooks_path}")
        else:
            print("  ✓ Git hooks path already configured")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error configuring Git hooks: {e}")
        sys.exit(1)

    print("\nDone. pre-commit wrappers are installed globally.")
    print("- They run pre-commit in repos with .pre-commit-config.yaml")
    print(
        "- The commit-msg wrapper will also run Captain's Log if installed at ~/.captains-log"
    )


def main():
    """Main entry point for the captains-log CLI."""
    try:
        args, log_level = cli_logging.split_log_level_args(sys.argv[1:])
    except ValueError as exc:
        cli_logging.error(str(exc))
        sys.exit(1)
    cli_logging.configure_log_level(log_level)

    if len(args) < 1:
        print("Captain's Log - Automatically log your git commits")
        print(f"Version: {__version__}")
        print()
        print("Usage:")
        print(
            "  captains-log [--log-level compact|verbose|debug] setup"
            " - Set up Captain's Log"
        )
        print(
            "  captains-log install-precommit-hooks - Install global pre-commit wrappers"
        )
        print("  captains-log --version             - Show version")
        print()
        print("After setup, use these commands:")
        print("  btw 'your note'              - Add manual log entries")
        print("  wtf 'what broke'             - Add issue entries")
        print("  wnext 'what next'            - Add entries to 'Whats next' section")
        print("  stone 'milestone'            - Add entries to yearly milestones file")
        print()
        sys.exit(0)

    command = args[0]

    if command in ("--version", "-v"):
        print_version()
    elif command == "setup":
        setup()
    elif command == "install-precommit-hooks":
        install_precommit_hooks()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: setup, install-precommit-hooks, --version")
        sys.exit(1)


if __name__ == "__main__":
    main()

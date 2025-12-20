#!/usr/bin/env python3
"""
Captain's Log CLI - Main command-line interface

Provides setup and configuration commands for Captain's Log.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__


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

    # Copy commit-msg hook
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

    if commit_msg_source.exists():
        commit_msg_dest = git_hooks_dir / "commit-msg"
        shutil.copy2(commit_msg_source, commit_msg_dest)
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
    print("  captains-log --version       - Show version")
    print("  captains-log setup           - Run setup again")
    print()
    print("Next steps:")
    print(f"  1. Edit your config: {config_file}")
    print("  2. Set up your log repository")
    print("  3. Start committing! Your commits will be logged automatically")
    print()


def main():
    """Main entry point for the captains-log CLI."""
    if len(sys.argv) < 2:
        print("Captain's Log - Automatically log your git commits")
        print(f"Version: {__version__}")
        print()
        print("Usage:")
        print("  captains-log setup           - Set up Captain's Log")
        print("  captains-log --version       - Show version")
        print()
        print("After setup, use these commands:")
        print("  btw 'your note'              - Add manual log entries")
        print("  wtf 'what broke'             - Add issue entries")
        sys.exit(0)

    command = sys.argv[1]

    if command in ("--version", "-v"):
        print_version()
    elif command == "setup":
        setup()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: setup, --version")
        sys.exit(1)


if __name__ == "__main__":
    main()

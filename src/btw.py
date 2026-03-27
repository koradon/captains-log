#!/usr/bin/env python3
"""
Refactored btw.py using domain-driven design modules.

BTW (By The Way) - Quick log entry tool for Captain's Log
Usage: btw "What I have done"
"""

import sys
from datetime import date
from pathlib import Path

# Domain imports
from src import cli_logging
from src.config import load_config
from src.entries import EntryProcessor
from src.git import GitOperations
from src.logs import LogManager
from src.projects import ProjectFinder


def add_manual_entry(entry_text: str):
    """Add a manual entry to the daily log under 'other' category.

    Args:
        entry_text: Text for the manual entry
    """
    # Load configuration
    config = load_config()

    # Find project from current working directory
    project_finder = ProjectFinder(config)
    cwd = Path.cwd()
    project = project_finder.find_project(str(cwd))

    # Get log file information
    log_manager = LogManager(config)
    log_info = log_manager.get_log_file_info(project)

    # Load existing log data
    log_data = log_manager.load_log(log_info)

    # Process the manual entry
    entry_processor = EntryProcessor()
    category = "other"

    # Get or create entries for the 'other' category
    other_entries = log_data.get_repo_entries(category)

    # Add the manual entry
    updated_entries = entry_processor.add_manual_entry(other_entries, entry_text)

    # Check if entry was actually added (avoid duplicates)
    if len(updated_entries) > len(other_entries):
        # Update log data
        log_data.set_repo_entries(category, updated_entries)
        # Save the updated log with 'other' at the end
        log_manager.save_log(log_info, log_data)

        # Commit and push if we have a git repository
        if log_info.has_git_repo:
            git_ops = GitOperations(log_info.log_repo_path)
            commit_message = f"Add manual entry to {project.name} logs for {date.today().isoformat()}"
            git_ops.commit_and_push(commit_message)

        cli_logging.success(f"Added entry to {project.name} log: {entry_text}")
    else:
        cli_logging.warning(f"Entry already exists in {project.name} log: {entry_text}")


def main():
    """Main entry point for the btw script."""
    try:
        args, log_level = cli_logging.split_log_level_args(sys.argv[1:])
    except ValueError as exc:
        cli_logging.error(str(exc))
        sys.exit(1)
    cli_logging.configure_log_level(log_level)

    # Check for version flag
    if len(args) > 0 and args[0] in ("--version", "-v"):
        from . import __version__

        print(f"Captain's Log (btw) v{__version__}")
        sys.exit(0)

    if len(args) < 1:
        print('Usage: btw "What I have done"')
        print('       btw --log-level debug "What I have done"')
        print('Example: btw "Reviewed the new API documentation"')
        sys.exit(1)

    # Join all arguments to allow for entries without quotes
    entry_text = " ".join(args)

    if not entry_text.strip():
        print("Error: Entry text cannot be empty")
        sys.exit(1)

    try:
        cli_logging.verbose("Processing manual entry update...")
        add_manual_entry(entry_text)
    except Exception as e:
        cli_logging.error(f"Error adding entry: {e}")
        cli_logging.debug(
            f"Debug context: cwd={Path.cwd()}, log_level={cli_logging.get_log_level()}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
WTF (What The Fault) - Quick log entry tool for Captain's Log

WTF - Quick log entry tool for issues and bugs
Usage: wtf "What broke or got weird"
"""

import sys
from datetime import date
from pathlib import Path

# Domain imports
from src.config import load_config
from src.entries import EntryProcessor
from src.git import GitOperations
from src.logs import LogManager
from src.projects import ProjectFinder


def add_wtf_entry(entry_text: str):
    """Add a manual entry to the daily log under 'What Broke or Got Weird' section.

    Args:
        entry_text: Text for the wtf entry
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

    # Get current "What Broke" entries
    wtf_entries_before = len(log_data.what_broke)

    # Format and add the manual entry
    formatted_entry = entry_processor.formatter.format_manual_entry(entry_text)
    log_data.add_what_broke_entry(formatted_entry)

    # Check if entry was actually added (avoid duplicates)
    if len(log_data.what_broke) > wtf_entries_before:
        # Save the updated log
        log_manager.save_log(log_info, log_data)

        # Commit and push if we have a git repository
        if log_info.has_git_repo and log_info.log_repo_path:
            git_ops = GitOperations(log_info.log_repo_path)
            commit_message = (
                f"Add WTF entry to {project.name} logs for {date.today().isoformat()}"
            )
            git_ops.commit_and_push(log_info.file_path, commit_message)

        print(f"Added WTF entry to {project.name} log: {entry_text}")
    else:
        print(f"Entry already exists in {project.name} log: {entry_text}")


def main():
    """Main entry point for the wtf script."""
    # Check for version flag
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-v"):
        from . import __version__

        print(f"Captain's Log (wtf) v{__version__}")
        sys.exit(0)

    if len(sys.argv) < 2:
        print('Usage: wtf "What broke or got weird"')
        print('Example: wtf "API endpoint started returning 500 errors"')
        sys.exit(1)

    # Join all arguments to allow for entries without quotes
    entry_text = " ".join(sys.argv[1:])

    if not entry_text.strip():
        print("Error: Entry text cannot be empty")
        sys.exit(1)

    try:
        add_wtf_entry(entry_text)
    except Exception as e:
        print(f"Error adding entry: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

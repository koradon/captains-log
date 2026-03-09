#!/usr/bin/env python3
"""
WNEXT - Quick entry tool for the "Whats next" section.

Usage:
    wnext "What to do next"
    wnext --other "General next action"
    wnext --project some_project "Next action for specific project"
"""

import sys
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

from src.config import load_config
from src.entries import EntryProcessor
from src.git import GitOperations
from src.logs import LogManager
from src.projects import ProjectFinder


def add_what_next_entry(entry_text: str, project_name: Optional[str], use_other: bool):
    """Add an entry to the 'Whats next' section."""
    config = load_config()

    project_finder = ProjectFinder(config)
    cwd = Path.cwd()

    # Determine target project
    if project_name is not None:
        project = project_finder.get_project_by_name(project_name)
        if project is None:
            print(f"Error: Project '{project_name}' not found in configuration")
            sys.exit(1)
    else:
        project = project_finder.find_project(str(cwd))

    log_manager = LogManager(config)
    log_info = log_manager.get_log_file_info(project)

    # Load existing log data
    log_data = log_manager.load_log(log_info)

    # Determine subsection name within "Whats next"
    section_name = "other" if use_other else project.name

    entry_processor = EntryProcessor()

    # Get existing entries for the subsection
    existing_entries = log_data.get_what_next_entries(section_name)

    # Add the manual entry (avoids duplicates)
    updated_entries = entry_processor.add_manual_entry(existing_entries, entry_text)

    if len(updated_entries) > len(existing_entries):
        log_data.set_what_next_entries(section_name, updated_entries)

        # Save the updated log
        log_manager.save_log(log_info, log_data)

        # Commit and push if we have a git repository
        if log_info.has_git_repo and log_info.log_repo_path:
            git_ops = GitOperations(log_info.log_repo_path)
            commit_message = f"Add What Next entry to {project.name} logs for {date.today().isoformat()}"
            git_ops.commit_and_push(commit_message)

        print(
            f"Added 'Whats next' entry to {project.name} "
            f"({'other' if use_other else section_name}): {entry_text}"
        )
    else:
        print(
            f"'Whats next' entry already exists in {project.name} "
            f"({'other' if use_other else section_name}): {entry_text}"
        )


def _parse_args(argv: List[str]) -> Tuple[str, Optional[str], bool]:
    """Simple argument parser for wnext."""
    project_name: str | None = None
    use_other = False
    message_parts: list[str] = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--project", "-p"):
            if use_other:
                print("Error: --project/-p and --other/-o cannot be used together")
                sys.exit(1)
            i += 1
            if i >= len(argv):
                print("Error: --project/-p requires a project name")
                sys.exit(1)
            project_name = argv[i]
        elif arg in ("--other", "-o"):
            if project_name is not None:
                print("Error: --project/-p and --other/-o cannot be used together")
                sys.exit(1)
            use_other = True
        else:
            message_parts.append(arg)
        i += 1

    message = " ".join(message_parts).strip()
    if not message:
        print('Usage: wnext [--project/-p name | --other/-o] "What to do next"')
        sys.exit(1)

    return message, project_name, use_other


def main():
    """Main entry point for the wnext script."""
    # Version flag
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-v"):
        from . import __version__

        print(f"Captain's Log (wnext) v{__version__}")
        sys.exit(0)

    if len(sys.argv) < 2:
        print('Usage: wnext [--project/-p name | --other/-o] "What to do next"')
        print('Example: wnext "Plan sprint backlog refinement"')
        print('         wnext --other "Remember to update wiki"')
        sys.exit(1)

    message, project_name, use_other = _parse_args(sys.argv[1:])

    try:
        add_what_next_entry(message, project_name, use_other)
    except Exception as e:
        print(f"Error adding What Next entry: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

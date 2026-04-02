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

from src import cli_logging
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

    # Determine target project (for choosing the log location)
    if project_name is not None:
        project = project_finder.get_project_by_name(project_name)
        if project is None:
            cli_logging.error(
                f"Error: Project '{project_name}' not found in configuration"
            )
            sys.exit(1)
    else:
        project = project_finder.find_project(str(cwd))

    log_manager = LogManager(config)
    log_info = log_manager.get_log_file_info(project)

    # Load existing log data
    log_data = log_manager.load_log(log_info)

    # Determine subsection name within "Whats next".
    # For commits, the "What I did" section uses the repository name passed
    # from the git hook (e.g. order-service) even when the project (and thus
    # log file location) corresponds to a parent mono-repo (e.g. lulu).
    #
    # We mirror that behaviour here by:
    # - Keeping the project (and log file) resolution based on configuration
    #   via ProjectFinder (so entries still go under the lulu project logs).
    # - Using the git repository name, when available, as the default section
    #   name within "Whats next" so that nested repos like order-service get
    #   their own subsection under the parent project log.

    def _find_git_root(path: Path) -> Optional[Path]:
        current = path
        while True:
            if (current / ".git").is_dir():
                return current

            parent = current.parent
            if parent == current:
                return None
            current = parent

    git_root = _find_git_root(cwd)
    default_section = git_root.name if git_root is not None else project.name

    if use_other:
        section_name = "other"
    elif project_name is not None:
        # When the user explicitly selects a project, keep the traditional
        # behaviour of using that project name as the subsection.
        section_name = project.name
    else:
        section_name = default_section

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

        cli_logging.success(
            f"Added 'Whats next' entry to {project.name} "
            f"({'other' if use_other else section_name}): {entry_text}"
        )
    else:
        cli_logging.warning(
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
                cli_logging.error(
                    "Error: --project/-p and --other/-o cannot be used together"
                )
                sys.exit(1)
            i += 1
            if i >= len(argv):
                cli_logging.error("Error: --project/-p requires a project name")
                sys.exit(1)
            project_name = argv[i]
        elif arg in ("--other", "-o"):
            if project_name is not None:
                cli_logging.error(
                    "Error: --project/-p and --other/-o cannot be used together"
                )
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
    try:
        args, log_level = cli_logging.split_log_level_args(sys.argv[1:])
    except ValueError as exc:
        cli_logging.error(str(exc))
        sys.exit(1)
    cli_logging.configure_log_level(log_level)

    # Version flag
    if len(args) > 0 and args[0] in ("--version", "-v"):
        from . import __version__

        print(f"Captain's Log (wnext) v{__version__}")
        sys.exit(0)

    if len(args) < 1:
        print('Usage: wnext [--project/-p name | --other/-o] "What to do next"')
        print(
            '       wnext --log-level debug [--project/-p name | --other/-o] "What to do next"'
        )
        print('Example: wnext "Plan sprint backlog refinement"')
        print('         wnext --other "Remember to update wiki"')
        sys.exit(1)

    message, project_name, use_other = _parse_args(args)

    try:
        cli_logging.verbose("Processing 'Whats next' entry update...")
        add_what_next_entry(message, project_name, use_other)
    except Exception as e:
        cli_logging.error(f"Error adding What Next entry: {e}")
        cli_logging.debug(
            f"Debug context: cwd={Path.cwd()}, log_level={cli_logging.get_log_level()}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

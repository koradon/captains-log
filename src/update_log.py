#!/usr/bin/env python3
"""
Refactored update_log.py using domain-driven design modules.

This script processes git commit information and updates daily log files.
"""

import sys
from datetime import date
from pathlib import Path

# Domain imports
from src.config import load_config
from src.entries import EntryProcessor
from src.git import CommitParser, GitOperations
from src.logs import LogManager
from src.projects import ProjectFinder


# Backward compatibility exports for existing tests
def load_config_legacy():
    """Legacy function for backward compatibility."""
    return load_config()


def find_project(repo_path, config):
    """Legacy function for backward compatibility."""
    from src.config.config_models import Config

    if not isinstance(config, Config):
        config = Config.from_dict(config)

    finder = ProjectFinder(config)
    project_info = finder.find_project(repo_path)
    return project_info.name


def load_log(file_path):
    """Legacy function for backward compatibility."""
    from src.logs import LogParser

    parser = LogParser()
    log_data = parser.parse_log_file(file_path)
    return log_data.repos


def parse_commit_entry(entry):
    """Legacy function for backward compatibility."""
    return CommitParser.parse_commit_entry(entry)


def update_commit_entries(entries, new_sha, new_msg):
    """Legacy function for backward compatibility."""
    processor = EntryProcessor()
    return processor.update_commit_entries(entries, new_sha, new_msg)


def save_log(file_path, repos):
    """Legacy function for backward compatibility."""
    from src.logs import LogData, LogWriter

    writer = LogWriter()
    log_data = LogData(repos=repos)
    writer.write_log_file(file_path, log_data)


def commit_and_push(log_repo_path, file_path, commit_msg):
    """Legacy function for backward compatibility."""
    git_ops = GitOperations(log_repo_path)
    git_ops.commit_and_push(file_path, commit_msg)


def get_log_repo_and_path(project, config):
    """Legacy function for backward compatibility."""
    from src.config.config_models import Config
    from src.projects.project_models import ProjectInfo

    if not isinstance(config, Config):
        config = Config.from_dict(config)

    # Create a minimal ProjectInfo for the legacy interface
    project_config = config.get_project_config(project)
    project_info = ProjectInfo(name=project, config=project_config, base_dir=Path.cwd())

    manager = LogManager(config)
    log_info = manager.get_log_file_info(project_info)

    return log_info.log_repo_path, log_info.file_path


# Legacy constants for backward compatibility
BASE_DIR = Path.home() / ".captains-log" / "projects"
CONFIG_FILE = Path.home() / ".captains-log" / "config.yml"
HEADER = "# What I did\n\n"
FOOTER = "# Whats next\n\n\n# What Broke or Got Weird\n"


def main():
    """Main entry point for the update log script."""
    # Check for version flag
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-v"):
        from . import __version__

        print(f"Captain's Log (update_log) v{__version__}")
        sys.exit(0)

    if len(sys.argv) < 5:
        print(
            "Usage: update_log.py <repo_name> <repo_path> <commit_sha> <commit_message>"
        )
        return

    repo_name = sys.argv[1]
    repo_path = sys.argv[2]
    commit_sha = sys.argv[3]
    commit_msg = sys.argv[4]

    try:
        # Load configuration
        config = load_config()

        # Check if we should skip this commit
        if CommitParser.should_skip_commit(
            commit_sha,
            repo_path,
            str(config.global_log_repo) if config.global_log_repo else None,
        ):
            if not CommitParser.is_valid_commit_sha(commit_sha):
                print("Skipping log update: No valid commit SHA")
            else:
                print("Skipping log update: Running from within log repository")
            return

        # Find project information
        project_finder = ProjectFinder(config)
        project = project_finder.find_project(repo_path)

        # Get log file information
        log_manager = LogManager(config)
        log_info = log_manager.get_log_file_info(project)

        # Load existing log data
        log_data = log_manager.load_log(log_info)

        # Process the new commit entry
        entry_processor = EntryProcessor()

        # Get or create repository entries
        repo_entries = log_data.get_repo_entries(repo_name)

        # Update with new commit
        updated_entries = entry_processor.update_commit_entries(
            repo_entries, commit_sha, commit_msg
        )

        # Update log data
        log_data.set_repo_entries(repo_name, updated_entries)

        # Save the updated log
        log_manager.save_log(log_info, log_data)

        # Commit and push if we have a git repository
        if log_info.has_git_repo:
            git_ops = GitOperations(log_info.log_repo_path)
            commit_message = (
                f"Update {project.name} logs for {date.today().isoformat()}"
            )
            git_ops.commit_and_push(log_info.file_path, commit_message)

        print(f"Updated log for {repo_name} in project {project.name}")

    except Exception as e:
        print(f"Error updating log: {e}")
        # Don't exit with error code to avoid breaking git operations
        sys.exit(0)


if __name__ == "__main__":
    main()

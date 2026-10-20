#!/usr/bin/env python3
"""
Refactored update_log.py using domain-driven design modules.

This script processes git commit information and updates daily log files.
"""

import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

# Domain imports
from src import cli_logging
from src.config import load_config
from src.entries import EntryProcessor
from src.git import CommitParser, GitOperations
from src.logs import LogManager
from src.projects import ProjectFinder
from src.publication import PublicationRun


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


def commit_and_push(log_repo_path, commit_msg):
    """Legacy function for backward compatibility."""
    git_ops = GitOperations(log_repo_path)
    return git_ops.commit_and_push(commit_msg)


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
    try:
        args, log_level = cli_logging.split_log_level_args(sys.argv[1:])
    except ValueError as exc:
        _argument_error(str(exc))
    cli_logging.configure_log_level(log_level)

    # Check for version flag
    if len(args) > 0 and args[0] in ("--version", "-v"):
        from . import __version__

        print(f"Captain's Log (update_log) v{__version__}")
        sys.exit(0)

    if len(args) < 4:
        _argument_error(
            "Usage: update_log.py [--log-level compact|verbose|debug] "
            "<repo_name> <repo_path> <commit_sha> <commit_message>"
        )

    repo_name = args[0]
    repo_path = args[1]
    commit_sha = args[2]
    commit_msg = args[3]

    run = PublicationRun(repo_name, commit_sha)
    with redirect_stdout(run), redirect_stderr(run):
        status = _update(repo_name, repo_path, commit_sha, commit_msg, run)
        run.exit_status = status
        print(f"Run finished with exit_status={status}")
        run.flush()
    if status:
        raise SystemExit(status)


def _argument_error(message):
    run = PublicationRun("unknown", "unknown")
    run.stage = "arguments"
    run.exit_status = 2
    with redirect_stdout(run):
        print(message)
    raise SystemExit(2)


def _update(repo_name, repo_path, commit_sha, commit_msg, run):
    saved = False
    try:
        config = load_config()
        if CommitParser.should_skip_commit(
            commit_sha,
            repo_path,
            str(config.global_log_repo) if config.global_log_repo else None,
        ):
            if not CommitParser.is_valid_commit_sha(commit_sha):
                print("Skipping log update: No valid commit SHA")
            else:
                print("Skipping log update: Running from within log repository")
            return 0

        run.stage = "project"
        project = ProjectFinder(config).find_project(repo_path)
        if project.is_private:
            print("Skipping log update: repository is private")
            return 0

        log_manager = LogManager(config)
        log_info = log_manager.get_log_file_info(project)
        # A project-specific log repo also needs the recursion guard.
        if (
            log_info.log_repo_path
            and Path(repo_path).resolve() == log_info.log_repo_path.resolve()
        ):
            print("Skipping log update: Running from within log repository")
            return 0
        run.start_pending(log_info.log_repo_path, log_info.file_path)
        git_ops = None
        if log_info.has_git_repo and log_info.log_repo_path:
            git_ops = GitOperations(log_info.log_repo_path)
            run.git_ops = git_ops
            if git_ops.wait_for_locks():
                git_ops.stage = "pull"
                git_ops.pull()
            # A failed pull must not prevent saving the source entry locally.
            # commit_and_push will expose a failed publication (or recover later).
            run.git_ops = None

        run.stage = "read"
        log_data = log_manager.load_log(log_info)
        processor = EntryProcessor()
        updated = processor.update_commit_entries(
            log_data.get_repo_entries(repo_name),
            commit_sha,
            commit_msg,
        )
        log_data.set_repo_entries(repo_name, updated)
        run.stage = "save"
        log_manager.save_log(log_info, log_data)
        saved = True
        run.update_pending(saved_locally=True)
        print(f"Saved locally for {repo_name} in project {project.name}")

        if git_ops is None:
            run.stage = "publication"
            run.exit_status = 2
            run.update_pending()
            print(
                f"Saved locally; NOT published: no Git log repository; pending={run.marker}"
            )
            return 2

        run.git_ops = git_ops
        commit_message = f"Update {project.name} logs for {date.today().isoformat()}"
        if not git_ops.commit_and_push(commit_message):
            run.exit_status = 1
            run.update_pending()
            print(f"Saved locally; NOT published; pending={run.marker}")
            return 1

        run.exit_status = 0
        run.published()
        print(f"Published log for {repo_name} in project {project.name}")
        return 0
    except Exception as exc:
        run.exit_status = 1
        print(f"Error updating log: {exc}")
        if not run.record:
            run.record = {"run": run.run_id, "repo": repo_name, "sha": commit_sha}
        if run.record:
            try:
                run.update_pending(saved_locally=saved, error=str(exc))
            except OSError as marker_error:
                print(f"Error recording pending publication: {marker_error}")
        print(
            "Saved locally; NOT published"
            if saved
            else "Log update failed before local save"
        )
        return 1


if __name__ == "__main__":
    main()

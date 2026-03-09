#!/usr/bin/env python3
"""
STONE - Yearly milestone entry tool for Captain's Log.

Usage:
    stone "Describe the milestone"

This command appends a milestone entry to a yearly `milestone.md` file
for the current project.
"""

from __future__ import annotations

import random
import sys
from datetime import date
from pathlib import Path

from src.config import Config, load_config
from src.git import GitOperations
from src.logs.log_manager import LogManager
from src.projects import ProjectFinder, ProjectInfo

EMOJIS: list[str] = ["🎯", "🏆", "🚀", "⭐️", "🎉", "📌"]


class MilestoneContext:
    """Resolved context for writing a milestone entry."""

    def __init__(
        self, config: Config, project: ProjectInfo, log_date: date, file_path: Path
    ):
        self.config = config
        self.project = project
        self.log_date = log_date
        self.file_path = file_path


def get_milestone_file_path(
    config: Config, project: ProjectInfo, log_date: date
) -> Path:
    """Compute the milestone file path for a project and date.

    Rules:
    - Determine the base directory using the same logic as daily logs:
      - project-specific log_repo, or
      - global_log_repo / project.name, or
      - default ~/.captains-log/projects/<project.name>
    - If `<base_dir>/<year>/` exists, use `<base_dir>/<year>/milestone.md`
    - Otherwise, use `<base_dir>/milestone.md`
    """
    log_manager = LogManager(config)

    # Mirror LogManager.get_log_file_info base directory logic
    log_repo_path = project.log_repo or config.global_log_repo
    base_dir = log_manager._get_base_directory(project, log_repo_path)  # type: ignore[attr-defined]

    year_str = str(log_date.year)
    year_dir = base_dir / year_str
    if year_dir.exists():
        return year_dir / "milestone.md"

    return base_dir / "milestone.md"


def append_milestone_entry(
    file_path: Path, log_date: date, text: str, emoji: str
) -> None:
    """Append a milestone entry to the given milestone file.

    The file has a flat structure:
    - First line: main header, e.g. '# Milestones 2026'
    - Following lines: bullet entries
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        content = file_path.read_text(encoding="utf-8")
    else:
        # Initialize file with a year-specific header
        header = f"# Milestones {log_date.year}\n\n"
        content = header

    entry_line = f"- {emoji} {log_date.isoformat()}: {text}"

    # Avoid duplicate entries
    if entry_line in content:
        return

    if content and not content.endswith("\n"):
        content += "\n"

    content += entry_line + "\n"
    file_path.write_text(content, encoding="utf-8")


def build_milestone_context() -> MilestoneContext:
    """Build the milestone context from the current working directory."""
    config = load_config()
    project_finder = ProjectFinder(config)
    cwd = Path.cwd()
    project = project_finder.find_project(str(cwd))
    today = date.today()
    file_path = get_milestone_file_path(config, project, today)
    return MilestoneContext(
        config=config, project=project, log_date=today, file_path=file_path
    )


def add_milestone_entry(entry_text: str) -> None:
    """High-level API to add a milestone entry for the current project."""
    ctx = build_milestone_context()
    emoji = random.choice(EMOJIS)

    append_milestone_entry(ctx.file_path, ctx.log_date, entry_text, emoji)

    # Commit and push if we have a git repository backing the logs
    log_repo_path = ctx.project.log_repo or ctx.config.global_log_repo
    if log_repo_path is not None:
        git_ops = GitOperations(log_repo_path)
        commit_message = (
            f"Add milestone entry to {ctx.project.name} for {ctx.log_date.year}"
        )
        git_ops.commit_and_push(commit_message)


def main() -> None:
    """Main entry point for the stone script."""
    # Version flag
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-v"):
        from . import __version__

        print(f"Captain's Log (stone) v{__version__}")
        raise SystemExit(0)

    if len(sys.argv) < 2:
        print('Usage: stone "Describe the milestone"')
        print('Example: stone "Shipped v1.0 of the product"')
        raise SystemExit(1)

    entry_text = " ".join(sys.argv[1:]).strip()
    if not entry_text:
        print("Error: Milestone text cannot be empty")
        raise SystemExit(1)

    try:
        add_milestone_entry(entry_text)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Error adding milestone entry: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

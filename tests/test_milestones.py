"""Tests for the stone (milestone) functionality."""

from datetime import date
from pathlib import Path

from src.config import Config, ProjectConfig
from src.projects import ProjectInfo
from src.stone import append_milestone_entry, get_milestone_file_path


def _make_project(tmp_path: Path) -> tuple[Config, ProjectInfo]:
    """Create a basic config and project for testing."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    config = Config.from_dict(
        {
            "global_log_repo": str(tmp_path / "logs"),
            "projects": {"test-project": str(project_root)},
        }
    )

    project_config = ProjectConfig(root=project_root)
    project = ProjectInfo(
        name="test-project",
        config=project_config,
        base_dir=project_root,
    )
    return config, project


def test_get_milestone_file_path_uses_year_directory_when_present(tmp_path):
    """When a year directory exists, milestones go under <base>/<year>/milestone.md."""
    config, project = _make_project(tmp_path)

    # Determine base directory the same way LogManager does
    base_dir = config.global_log_repo / project.name  # type: ignore[operator]
    year_dir = base_dir / "2026"
    year_dir.mkdir(parents=True)

    path = get_milestone_file_path(config, project, date(2026, 5, 1))

    assert path == year_dir / "milestone.md"


def test_get_milestone_file_path_falls_back_to_base_directory(tmp_path):
    """When year directory does not exist, milestones use <base>/milestone.md."""
    config, project = _make_project(tmp_path)

    base_dir = config.global_log_repo / project.name  # type: ignore[operator]
    base_dir.mkdir(parents=True)

    path = get_milestone_file_path(config, project, date(2026, 1, 10))

    assert path == base_dir / "milestone.md"


def test_append_milestone_entry_creates_file_with_header_and_entry(tmp_path):
    """First milestone creates file with header and a single entry."""
    milestone_file = tmp_path / "milestone.md"

    append_milestone_entry(milestone_file, date(2026, 3, 9), "First big win", "🎯")

    content = milestone_file.read_text()
    assert "# Milestones 2026" in content
    assert "- 🎯 2026-03-09: First big win" in content


def test_append_milestone_entry_appends_without_duplicates(tmp_path):
    """Subsequent milestones append new bullets and avoid duplicates."""
    milestone_file = tmp_path / "milestone.md"
    d = date(2026, 3, 9)

    append_milestone_entry(milestone_file, d, "First big win", "🎯")
    append_milestone_entry(milestone_file, d, "Second big win", "🚀")
    # Duplicate of first entry should be ignored
    append_milestone_entry(milestone_file, d, "First big win", "🎯")

    content = milestone_file.read_text().splitlines()

    header_lines = [line for line in content if line.startswith("# Milestones")]
    assert len(header_lines) == 1

    bullet_lines = [line for line in content if line.startswith("- ")]
    assert "- 🎯 2026-03-09: First big win" in bullet_lines
    assert "- 🚀 2026-03-09: Second big win" in bullet_lines
    # Only two unique entries
    assert len(bullet_lines) == 2

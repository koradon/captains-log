"""Tests for the stone (milestone) functionality."""

from datetime import date
from pathlib import Path

import pytest

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


def test_add_milestone_entry_writes_entry_and_commits(tmp_path, monkeypatch):
    """add_milestone_entry writes a milestone and commits when log_repo is set."""
    import src.stone as stone

    log_repo_path = tmp_path / "logs"
    milestone_file = log_repo_path / "milestone.md"

    class DummyConfig:
        def __init__(self) -> None:
            self.global_log_repo = log_repo_path

    class DummyProject:
        def __init__(self) -> None:
            self.name = "test-project"
            self.log_repo = log_repo_path

    ctx = stone.MilestoneContext(
        config=DummyConfig(),
        project=DummyProject(),
        log_date=date(2026, 3, 9),
        file_path=milestone_file,
    )

    def fake_build_context() -> "stone.MilestoneContext":
        return ctx

    created: dict[str, object] = {}

    class DummyGitOperations:
        def __init__(self, path) -> None:
            from pathlib import Path as _Path

            created["path"] = _Path(path)

        def commit_and_push(self, message: str) -> None:
            created["message"] = message

    monkeypatch.setattr(stone, "build_milestone_context", fake_build_context)
    monkeypatch.setattr(stone, "GitOperations", DummyGitOperations)
    monkeypatch.setattr(stone.random, "choice", lambda seq: "🎯")

    stone.add_milestone_entry("Big win")

    content = milestone_file.read_text(encoding="utf-8")
    assert "- 🎯 2026-03-09: Big win" in content
    assert created["path"] == log_repo_path
    assert created["message"] == "Add milestone entry to test-project for 2026"


def test_add_milestone_entry_without_log_repo_does_not_commit(tmp_path, monkeypatch):
    """When no log_repo/global_log_repo is configured, no git operations are run."""
    import src.stone as stone

    milestone_file = tmp_path / "milestone.md"

    class DummyConfig:
        def __init__(self) -> None:
            self.global_log_repo = None

    class DummyProject:
        def __init__(self) -> None:
            self.name = "test-project"
            self.log_repo = None

    ctx = stone.MilestoneContext(
        config=DummyConfig(),
        project=DummyProject(),
        log_date=date(2026, 3, 9),
        file_path=milestone_file,
    )

    monkeypatch.setattr(stone, "build_milestone_context", lambda: ctx)

    called = {"init": False}

    class DummyGitOperations:
        def __init__(self, path) -> None:
            called["init"] = True

        def commit_and_push(
            self, message: str
        ) -> None:  # pragma: no cover - should not run
            raise AssertionError("commit_and_push should not be called")

    monkeypatch.setattr(stone, "GitOperations", DummyGitOperations)
    monkeypatch.setattr(stone.random, "choice", lambda seq: "🎯")

    stone.add_milestone_entry("Big win")

    assert milestone_file.exists()
    assert called["init"] is False


def test_main_version_flag_prints_version_and_exits(monkeypatch, capsys):
    """stone --version prints version and exits with code 0."""
    import src.stone as stone

    monkeypatch.setattr(stone.sys, "argv", ["stone", "--version"])

    with pytest.raises(SystemExit) as exc:
        stone.main()

    captured = capsys.readouterr()
    assert "Captain's Log (stone) v" in captured.out
    assert exc.value.code == 0


def test_main_without_args_shows_usage_and_exits(monkeypatch, capsys):
    """stone with no args prints usage and exits with code 1."""
    import src.stone as stone

    monkeypatch.setattr(stone.sys, "argv", ["stone"])

    with pytest.raises(SystemExit) as exc:
        stone.main()

    captured = capsys.readouterr()
    assert "Usage: stone" in captured.out
    assert exc.value.code == 1


def test_main_rejects_empty_milestone_text(monkeypatch, capsys):
    """stone with only whitespace text exits with code 1."""
    import src.stone as stone

    monkeypatch.setattr(stone.sys, "argv", ["stone", "   "])

    with pytest.raises(SystemExit) as exc:
        stone.main()

    captured = capsys.readouterr()
    assert "Milestone text cannot be empty" in captured.out
    assert exc.value.code == 1


def test_main_calls_add_milestone_entry(monkeypatch):
    """stone 'some text' calls add_milestone_entry with joined text."""
    import src.stone as stone

    recorded: dict[str, str] = {}

    def fake_add_milestone_entry(text: str) -> None:
        recorded["text"] = text

    monkeypatch.setattr(stone, "add_milestone_entry", fake_add_milestone_entry)
    monkeypatch.setattr(stone.sys, "argv", ["stone", "First", "big", "win"])

    stone.main()

    assert recorded["text"] == "First big win"


def test_append_milestone_entry_adds_newline_if_missing(tmp_path):
    """Append when file lacks trailing newline inserts one before new entry."""
    from src.stone import append_milestone_entry as append_entry

    milestone_file = tmp_path / "milestone.md"
    # Existing content without a trailing newline
    milestone_file.write_text(
        "# Milestones 2026\n\n- 🎯 2026-03-09: First big win", encoding="utf-8"
    )

    append_entry(milestone_file, date(2026, 3, 10), "Second big win", "🚀")

    content = milestone_file.read_text(encoding="utf-8")
    assert "- 🎯 2026-03-09: First big win\n- 🚀 2026-03-10: Second big win" in content


def test_build_milestone_context_uses_loaded_config_and_project(tmp_path, monkeypatch):
    """build_milestone_context wires together config, project and path."""
    import src.stone as stone

    dummy_config = object()

    class DummyProject:
        def __init__(self) -> None:
            self.name = "test-project"
            self.log_repo = None

    dummy_project = DummyProject()
    fixed_date = date(2026, 3, 10)
    milestone_path = tmp_path / "milestone.md"

    recorded: dict[str, object] = {}

    def fake_load_config():
        return dummy_config

    class DummyProjectFinder:
        def __init__(self, cfg) -> None:
            recorded["config"] = cfg

        def find_project(self, root: str):
            recorded["root"] = root
            return dummy_project

    def fake_get_milestone_file_path(config, project, log_date):
        recorded["file_args"] = (config, project, log_date)
        return milestone_path

    class DummyDate:
        @staticmethod
        def today():
            return fixed_date

    monkeypatch.setattr(stone, "load_config", fake_load_config)
    monkeypatch.setattr(stone, "ProjectFinder", DummyProjectFinder)
    monkeypatch.setattr(stone, "get_milestone_file_path", fake_get_milestone_file_path)
    monkeypatch.setattr(stone, "date", DummyDate)

    ctx = stone.build_milestone_context()

    assert ctx.config is dummy_config
    assert ctx.project is dummy_project
    assert ctx.log_date == fixed_date
    assert ctx.file_path == milestone_path
    assert recorded["file_args"] == (dummy_config, dummy_project, fixed_date)

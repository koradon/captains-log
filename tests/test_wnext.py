#!/usr/bin/env python3
"""Tests for the wnext command functionality."""

from datetime import date

import pytest

from src.config.config_models import Config, ProjectConfig
from src.entries import EntryProcessor
from src.logs import LogData, LogManager, LogParser
from src.projects.project_models import ProjectInfo


def test_wnext_writes_to_whats_next_section(tmp_path, monkeypatch):
    """Ensure that 'Whats next' entries are written and parsed correctly."""
    # Arrange configuration and project
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    config = Config(
        global_log_repo=log_dir,
        projects={"test-project": ProjectConfig(root=tmp_path)},
    )

    project = ProjectInfo(
        name="test-project",
        config=ProjectConfig(root=tmp_path),
        base_dir=tmp_path,
    )

    manager = LogManager(config)
    log_info = manager.get_log_file_info(project)

    # Start with empty log data and a single What Next entry
    log_data = LogData()
    processor = EntryProcessor()
    section_name = project.name
    existing = log_data.get_what_next_entries(section_name)
    updated = processor.add_manual_entry(existing, "Plan next sprint")
    log_data.set_what_next_entries(section_name, updated)

    # Act: save and reload via parser
    manager.save_log(log_info, log_data)

    assert log_info.file_path.exists()
    parsed = LogParser.parse_log_file(log_info.file_path)

    assert parsed.what_next == {section_name: ["- Plan next sprint"]}
    content = log_info.file_path.read_text()
    assert "# Whats next" in content
    assert f"## {section_name}" in content
    assert "- Plan next sprint" in content


def test_parse_args_basic_message():
    """_parse_args joins remaining arguments into a message."""
    from src.wnext import _parse_args

    message, project_name, use_other = _parse_args(["Do", "the", "thing"])

    assert message == "Do the thing"
    assert project_name is None
    assert use_other is False


def test_parse_args_with_project():
    """_parse_args supports --project/-p with project name."""
    from src.wnext import _parse_args

    message, project_name, use_other = _parse_args(["--project", "proj", "Do", "it"])

    assert message == "Do it"
    assert project_name == "proj"
    assert use_other is False


def test_parse_args_with_other_flag():
    """_parse_args supports --other/-o without project."""
    from src.wnext import _parse_args

    message, project_name, use_other = _parse_args(["--other", "Do", "it"])

    assert message == "Do it"
    assert project_name is None
    assert use_other is True


def test_parse_args_conflicting_flags_exits(capsys):
    """Using --project and --other together exits with error."""
    from src import wnext

    with pytest.raises(SystemExit) as exc:
        wnext._parse_args(["--project", "proj", "--other", "Do it"])

    out = capsys.readouterr().out
    assert "cannot be used together" in out
    assert exc.value.code == 1


def test_parse_args_conflict_other_then_project_exits(capsys):
    """Using --other then --project exits with same conflict error (covers line 90-91)."""
    from src import wnext

    with pytest.raises(SystemExit) as exc:
        wnext._parse_args(["--other", "--project", "proj", "Do it"])

    out = capsys.readouterr().out
    assert "cannot be used together" in out
    assert exc.value.code == 1


def test_parse_args_missing_project_name_exits(capsys):
    """--project without a following name exits with error."""
    from src import wnext

    with pytest.raises(SystemExit) as exc:
        wnext._parse_args(["--project"])

    out = capsys.readouterr().out
    assert "requires a project name" in out
    assert exc.value.code == 1


def test_parse_args_missing_message_exits(capsys):
    """No message after flags prints usage and exits."""
    from src import wnext

    with pytest.raises(SystemExit) as exc:
        wnext._parse_args(["--other"])

    out = capsys.readouterr().out
    assert "Usage: wnext" in out
    assert exc.value.code == 1


def test_add_what_next_entry_adds_and_commits(tmp_path, monkeypatch, capsys):
    """add_what_next_entry writes entry, saves log, and commits when git repo exists."""
    import src.wnext as wnext

    fixed_date = date(2026, 3, 10)

    class DummyDate:
        @staticmethod
        def today():
            return fixed_date

    class DummyConfig:
        pass

    class DummyProject:
        def __init__(self) -> None:
            self.name = "test-project"

    recorded: dict[str, object] = {}

    class DummyProjectFinder:
        def __init__(self, config) -> None:
            recorded["config"] = config

        def find_project(self, root: str):
            recorded["root"] = root
            return DummyProject()

        def get_project_by_name(self, name: str):
            recorded["project_name_lookup"] = name
            return DummyProject()

    class DummyLogInfo:
        def __init__(self) -> None:
            self.has_git_repo = True
            self.log_repo_path = tmp_path / "logs"

    class DummyLogData:
        def __init__(self) -> None:
            self._what_next: dict[str, list[str]] = {}

        def get_what_next_entries(self, section: str):
            return list(self._what_next.get(section, []))

        def set_what_next_entries(self, section: str, entries):
            self._what_next[section] = list(entries)
            recorded["set_entries"] = (section, list(entries))

    class DummyLogManager:
        def __init__(self, config) -> None:
            recorded["manager_config"] = config

        def get_log_file_info(self, project):
            recorded["project"] = project
            return DummyLogInfo()

        def load_log(self, log_info):
            recorded["loaded"] = True
            return DummyLogData()

        def save_log(self, log_info, log_data):
            recorded["saved"] = True

    class DummyEntryProcessor:
        def add_manual_entry(self, entries, text: str):
            recorded["added_text"] = text
            return list(entries) + [f"- {text}"]

    class DummyGitOperations:
        def __init__(self, path):
            recorded["git_path"] = path

        def commit_and_push(self, message: str):
            recorded["git_message"] = message

    monkeypatch.setattr(wnext, "load_config", lambda: DummyConfig())
    monkeypatch.setattr(wnext, "ProjectFinder", DummyProjectFinder)
    monkeypatch.setattr(wnext, "LogManager", DummyLogManager)
    monkeypatch.setattr(wnext, "EntryProcessor", DummyEntryProcessor)
    monkeypatch.setattr(wnext, "GitOperations", DummyGitOperations)
    monkeypatch.setattr(wnext, "date", DummyDate)

    wnext.add_what_next_entry("Do something", project_name=None, use_other=False)

    out = capsys.readouterr().out
    assert "Added 'Whats next' entry to test-project" in out
    assert recorded.get("saved") is True
    assert recorded.get("git_path") == tmp_path / "logs"
    assert (
        recorded.get("git_message")
        == "Add What Next entry to test-project logs for 2026-03-10"
    )
    assert recorded.get("set_entries")[0] == "test-project"
    assert "- Do something" in recorded.get("set_entries")[1]


def test_add_what_next_entry_with_other_section(tmp_path, monkeypatch, capsys):
    """use_other=True writes to 'other' subsection."""
    import src.wnext as wnext

    class DummyConfig:
        pass

    class DummyProject:
        def __init__(self) -> None:
            self.name = "test-project"

    recorded: dict[str, object] = {}

    class DummyProjectFinder:
        def __init__(self, config) -> None:
            recorded["config"] = config

        def find_project(self, root: str):
            recorded["root"] = root
            return DummyProject()

    class DummyLogInfo:
        def __init__(self) -> None:
            self.has_git_repo = False
            self.log_repo_path = None

    class DummyLogData:
        def __init__(self) -> None:
            self._what_next: dict[str, list[str]] = {}

        def get_what_next_entries(self, section: str):
            return list(self._what_next.get(section, []))

        def set_what_next_entries(self, section: str, entries):
            self._what_next[section] = list(entries)
            recorded["set_entries"] = (section, list(entries))

    class DummyLogManager:
        def __init__(self, config) -> None:
            recorded["manager_config"] = config

        def get_log_file_info(self, project):
            recorded["project"] = project
            return DummyLogInfo()

        def load_log(self, log_info):
            recorded["loaded"] = True
            return DummyLogData()

        def save_log(self, log_info, log_data):
            recorded["saved"] = True

    class DummyEntryProcessor:
        def add_manual_entry(self, entries, text: str):
            recorded["added_text"] = text
            return list(entries) + [f"- {text}"]

    class DummyGitOperations:
        def __init__(self, path):
            recorded["git_path"] = path

        def commit_and_push(self, message: str):
            recorded["git_message"] = message

    monkeypatch.setattr(wnext, "load_config", lambda: DummyConfig())
    monkeypatch.setattr(wnext, "ProjectFinder", DummyProjectFinder)
    monkeypatch.setattr(wnext, "LogManager", DummyLogManager)
    monkeypatch.setattr(wnext, "EntryProcessor", DummyEntryProcessor)
    monkeypatch.setattr(wnext, "GitOperations", DummyGitOperations)

    wnext.add_what_next_entry("General thing", project_name=None, use_other=True)

    out = capsys.readouterr().out
    assert "('other" in out or "other" in out  # message mentions 'other' subsection
    assert recorded.get("set_entries")[0] == "other"
    # No git operations when has_git_repo is False
    assert recorded.get("git_message") is None


def test_add_what_next_entry_project_not_found_exits(monkeypatch, capsys):
    """If project name is not in config, add_what_next_entry exits with error."""
    import src.wnext as wnext

    class DummyConfig:
        pass

    class DummyProjectFinder:
        def __init__(self, config) -> None:
            self.config = config

        def get_project_by_name(self, name: str):
            return None

    monkeypatch.setattr(wnext, "load_config", lambda: DummyConfig())
    monkeypatch.setattr(wnext, "ProjectFinder", DummyProjectFinder)

    with pytest.raises(SystemExit) as exc:
        wnext.add_what_next_entry(
            "Do something", project_name="missing", use_other=False
        )

    out = capsys.readouterr().out
    assert "Project 'missing' not found" in out
    assert exc.value.code == 1


def test_add_what_next_entry_duplicate_does_not_save_or_commit(
    tmp_path, monkeypatch, capsys
):
    """If entry already exists, no save or git operations occur."""
    import src.wnext as wnext

    class DummyConfig:
        pass

    class DummyProject:
        def __init__(self) -> None:
            self.name = "test-project"

    recorded: dict[str, object] = {}

    class DummyProjectFinder:
        def __init__(self, config) -> None:
            recorded["config"] = config

        def find_project(self, root: str):
            recorded["root"] = root
            return DummyProject()

    class DummyLogInfo:
        def __init__(self) -> None:
            self.has_git_repo = True
            self.log_repo_path = tmp_path / "logs"

    class DummyLogData:
        def __init__(self) -> None:
            self._what_next: dict[str, list[str]] = {"test-project": ["- Existing"]}

        def get_what_next_entries(self, section: str):
            return list(self._what_next.get(section, []))

        def set_what_next_entries(self, section: str, entries):
            recorded["set_entries_called"] = True

    class DummyLogManager:
        def __init__(self, config) -> None:
            recorded["manager_config"] = config

        def get_log_file_info(self, project):
            recorded["project"] = project
            return DummyLogInfo()

        def load_log(self, log_info):
            recorded["loaded"] = True
            return DummyLogData()

        def save_log(self, log_info, log_data):
            recorded["saved"] = True

    class DummyEntryProcessor:
        def add_manual_entry(self, entries, text: str):
            # Return the same list to simulate no change
            return list(entries)

    class DummyGitOperations:
        def __init__(self, path):
            recorded["git_path"] = path

        def commit_and_push(self, message: str):
            recorded["git_message"] = message

    monkeypatch.setattr(wnext, "load_config", lambda: DummyConfig())
    monkeypatch.setattr(wnext, "ProjectFinder", DummyProjectFinder)
    monkeypatch.setattr(wnext, "LogManager", DummyLogManager)
    monkeypatch.setattr(wnext, "EntryProcessor", DummyEntryProcessor)
    monkeypatch.setattr(wnext, "GitOperations", DummyGitOperations)

    wnext.add_what_next_entry("Existing", project_name=None, use_other=False)

    out = capsys.readouterr().out
    assert "entry already exists" in out
    assert recorded.get("saved") is None
    assert recorded.get("git_message") is None


def test_main_version_flag_prints_version_and_exits(monkeypatch, capsys):
    """wnext --version prints version and exits with code 0."""
    import src.wnext as wnext

    monkeypatch.setattr(wnext.sys, "argv", ["wnext", "--version"])

    with pytest.raises(SystemExit) as exc:
        wnext.main()

    out = capsys.readouterr().out
    assert "Captain's Log (wnext) v" in out
    assert exc.value.code == 0


def test_main_without_args_shows_usage_and_exits(monkeypatch, capsys):
    """wnext with no args prints usage and exits with code 1."""
    import src.wnext as wnext

    monkeypatch.setattr(wnext.sys, "argv", ["wnext"])

    with pytest.raises(SystemExit) as exc:
        wnext.main()

    out = capsys.readouterr().out
    assert "Usage: wnext" in out
    assert exc.value.code == 1


def test_main_calls_add_what_next_entry(monkeypatch):
    """wnext 'some text' calls add_what_next_entry with parsed args."""
    import src.wnext as wnext

    recorded: dict[str, object] = {}

    def fake_add(message: str, project_name, use_other: bool) -> None:
        recorded["args"] = (message, project_name, use_other)

    monkeypatch.setattr(wnext, "add_what_next_entry", fake_add)
    monkeypatch.setattr(wnext.sys, "argv", ["wnext", "--project", "proj", "Do", "it"])

    wnext.main()

    assert recorded["args"] == ("Do it", "proj", False)


def test_main_handles_add_what_next_entry_error(monkeypatch, capsys):
    """If add_what_next_entry raises, main prints error and exits with code 1."""
    import src.wnext as wnext

    def boom(message: str, project_name, use_other: bool) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(wnext, "add_what_next_entry", boom)
    monkeypatch.setattr(wnext.sys, "argv", ["wnext", "Do", "it"])

    with pytest.raises(SystemExit) as exc:
        wnext.main()

    out = capsys.readouterr().out
    assert "Error adding What Next entry: boom" in out
    assert exc.value.code == 1

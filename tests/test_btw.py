from datetime import date

import pytest


def test_add_manual_entry_adds_and_commits(tmp_path, monkeypatch, capsys):
    """add_manual_entry writes entry, saves log, and commits when git repo exists."""
    import src.btw as btw

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

    class DummyLogInfo:
        def __init__(self) -> None:
            self.has_git_repo = True
            self.log_repo_path = tmp_path / "logs"

    class DummyLogData:
        def __init__(self) -> None:
            self._entries: dict[str, list[str]] = {"other": ["- old entry"]}

        def get_repo_entries(self, category: str):
            return list(self._entries.get(category, []))

        def set_repo_entries(self, category: str, entries):
            self._entries[category] = list(entries)
            recorded["set_entries"] = (category, list(entries))

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

    monkeypatch.setattr(btw, "load_config", lambda: DummyConfig())
    monkeypatch.setattr(btw, "ProjectFinder", DummyProjectFinder)
    monkeypatch.setattr(btw, "LogManager", DummyLogManager)
    monkeypatch.setattr(btw, "EntryProcessor", DummyEntryProcessor)
    monkeypatch.setattr(btw, "GitOperations", DummyGitOperations)
    monkeypatch.setattr(btw, "date", DummyDate)

    btw.add_manual_entry("Did a thing")

    out = capsys.readouterr().out
    assert "Added entry to test-project log: Did a thing" in out
    assert recorded.get("saved") is True
    assert recorded.get("git_path") == tmp_path / "logs"
    assert (
        recorded.get("git_message")
        == "Add manual entry to test-project logs for 2026-03-10"
    )
    assert recorded.get("set_entries")[0] == "other"
    assert "- Did a thing" in recorded.get("set_entries")[1]


def test_add_manual_entry_duplicate_does_not_save_or_commit(
    tmp_path, monkeypatch, capsys
):
    """If entry already exists, add_manual_entry only prints duplicate message."""
    import src.btw as btw

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
            self._entries: dict[str, list[str]] = {"other": ["- existing entry"]}

        def get_repo_entries(self, category: str):
            return list(self._entries.get(category, []))

        def set_repo_entries(self, category: str, entries):
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
            # Return the same list to simulate no change (duplicate)
            return list(entries)

    class DummyGitOperations:
        def __init__(self, path):
            recorded["git_path"] = path

        def commit_and_push(self, message: str):
            recorded["git_message"] = message

    monkeypatch.setattr(btw, "load_config", lambda: DummyConfig())
    monkeypatch.setattr(btw, "ProjectFinder", DummyProjectFinder)
    monkeypatch.setattr(btw, "LogManager", DummyLogManager)
    monkeypatch.setattr(btw, "EntryProcessor", DummyEntryProcessor)
    monkeypatch.setattr(btw, "GitOperations", DummyGitOperations)

    btw.add_manual_entry("existing entry")

    out = capsys.readouterr().out
    assert "Entry already exists in test-project log: existing entry" in out
    assert recorded.get("saved") is None
    assert recorded.get("git_message") is None


def test_main_version_flag_prints_version_and_exits(monkeypatch, capsys):
    """btw --version prints version and exits with code 0."""
    import src.btw as btw

    monkeypatch.setattr(btw.sys, "argv", ["btw", "--version"])

    with pytest.raises(SystemExit) as exc:
        btw.main()

    out = capsys.readouterr().out
    assert "Captain's Log (btw) v" in out
    assert exc.value.code == 0


def test_main_without_args_shows_usage_and_exits(monkeypatch, capsys):
    """btw with no args prints usage and exits with code 1."""
    import src.btw as btw

    monkeypatch.setattr(btw.sys, "argv", ["btw"])

    with pytest.raises(SystemExit) as exc:
        btw.main()

    out = capsys.readouterr().out
    assert "Usage: btw" in out
    assert exc.value.code == 1


def test_main_rejects_empty_entry_text(monkeypatch, capsys):
    """btw with only whitespace text exits with code 1."""
    import src.btw as btw

    monkeypatch.setattr(btw.sys, "argv", ["btw", "   "])

    with pytest.raises(SystemExit) as exc:
        btw.main()

    out = capsys.readouterr().out
    assert "Entry text cannot be empty" in out
    assert exc.value.code == 1


def test_main_calls_add_manual_entry(monkeypatch):
    """btw 'some text' calls add_manual_entry with joined text."""
    import src.btw as btw

    recorded: dict[str, str] = {}

    def fake_add_manual_entry(text: str) -> None:
        recorded["text"] = text

    monkeypatch.setattr(btw, "add_manual_entry", fake_add_manual_entry)
    monkeypatch.setattr(btw.sys, "argv", ["btw", "Did", "a", "thing"])

    btw.main()

    assert recorded["text"] == "Did a thing"


def test_main_handles_add_manual_entry_error(monkeypatch, capsys):
    """If add_manual_entry raises, main prints error and exits with code 1."""
    import src.btw as btw

    def boom(text: str) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(btw, "add_manual_entry", boom)
    monkeypatch.setattr(btw.sys, "argv", ["btw", "Do something"])

    with pytest.raises(SystemExit) as exc:
        btw.main()

    out = capsys.readouterr().out
    assert "Error adding entry: boom" in out
    assert exc.value.code == 1

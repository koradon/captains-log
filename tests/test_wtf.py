from datetime import date

import pytest


def test_add_wtf_entry_adds_and_commits(tmp_path, monkeypatch, capsys):
    """add_wtf_entry writes a WTF entry, saves log, and commits when git repo exists."""
    import src.wtf as wtf

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
            self.what_broke: list[str] = []

        def add_what_broke_entry(self, entry: str) -> None:
            self.what_broke.append(entry)

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

    class DummyFormatter:
        def format_manual_entry(self, text: str) -> str:
            recorded["formatted_text"] = text
            return f"- {text}"

    class DummyEntryProcessor:
        def __init__(self) -> None:
            self.formatter = DummyFormatter()

    class DummyGitOperations:
        def __init__(self, path):
            recorded["git_path"] = path

        def commit_and_push(self, message: str):
            recorded["git_message"] = message

    monkeypatch.setattr(wtf, "load_config", lambda: DummyConfig())
    monkeypatch.setattr(wtf, "ProjectFinder", DummyProjectFinder)
    monkeypatch.setattr(wtf, "LogManager", DummyLogManager)
    monkeypatch.setattr(wtf, "EntryProcessor", DummyEntryProcessor)
    monkeypatch.setattr(wtf, "GitOperations", DummyGitOperations)
    monkeypatch.setattr(wtf, "date", DummyDate)

    wtf.add_wtf_entry("Something broke")

    out = capsys.readouterr().out
    assert "Added WTF entry to test-project log: Something broke" in out
    assert recorded.get("saved") is True
    assert recorded.get("git_path") == tmp_path / "logs"
    assert (
        recorded.get("git_message")
        == "Add WTF entry to test-project logs for 2026-03-10"
    )
    assert recorded.get("formatted_text") == "Something broke"


def test_add_wtf_entry_duplicate_does_not_save_or_commit(tmp_path, monkeypatch, capsys):
    """If WTF entry already exists, add_wtf_entry only prints duplicate message."""
    import src.wtf as wtf

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
            self.what_broke: list[str] = ["- Existing issue"]

        def add_what_broke_entry(self, entry: str) -> None:
            # Do not modify list to simulate duplicate handling
            recorded["add_called"] = True

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

    class DummyFormatter:
        def format_manual_entry(self, text: str) -> str:
            recorded["formatted_text"] = text
            return f"- {text}"

    class DummyEntryProcessor:
        def __init__(self) -> None:
            self.formatter = DummyFormatter()

    class DummyGitOperations:
        def __init__(self, path):
            recorded["git_path"] = path

        def commit_and_push(self, message: str):
            recorded["git_message"] = message

    monkeypatch.setattr(wtf, "load_config", lambda: DummyConfig())
    monkeypatch.setattr(wtf, "ProjectFinder", DummyProjectFinder)
    monkeypatch.setattr(wtf, "LogManager", DummyLogManager)
    monkeypatch.setattr(wtf, "EntryProcessor", DummyEntryProcessor)
    monkeypatch.setattr(wtf, "GitOperations", DummyGitOperations)

    wtf.add_wtf_entry("Existing issue")

    out = capsys.readouterr().out
    assert "Entry already exists in test-project log: Existing issue" in out
    assert recorded.get("saved") is None
    assert recorded.get("git_message") is None


def test_main_version_flag_prints_version_and_exits(monkeypatch, capsys):
    """wtf --version prints version and exits with code 0."""
    import src.wtf as wtf

    monkeypatch.setattr(wtf.sys, "argv", ["wtf", "--version"])

    with pytest.raises(SystemExit) as exc:
        wtf.main()

    out = capsys.readouterr().out
    assert "Captain's Log (wtf) v" in out
    assert exc.value.code == 0


def test_main_without_args_shows_usage_and_exits(monkeypatch, capsys):
    """wtf with no args prints usage and exits with code 1."""
    import src.wtf as wtf

    monkeypatch.setattr(wtf.sys, "argv", ["wtf"])

    with pytest.raises(SystemExit) as exc:
        wtf.main()

    out = capsys.readouterr().out
    assert "Usage: wtf" in out
    assert exc.value.code == 1


def test_main_rejects_empty_entry_text(monkeypatch, capsys):
    """wtf with only whitespace text exits with code 1."""
    import src.wtf as wtf

    monkeypatch.setattr(wtf.sys, "argv", ["wtf", "   "])

    with pytest.raises(SystemExit) as exc:
        wtf.main()

    out = capsys.readouterr().out
    assert "Entry text cannot be empty" in out
    assert exc.value.code == 1


def test_main_calls_add_wtf_entry(monkeypatch):
    """wtf 'some text' calls add_wtf_entry with joined text."""
    import src.wtf as wtf

    recorded: dict[str, str] = {}

    def fake_add_wtf_entry(text: str) -> None:
        recorded["text"] = text

    monkeypatch.setattr(wtf, "add_wtf_entry", fake_add_wtf_entry)
    monkeypatch.setattr(wtf.sys, "argv", ["wtf", "Something", "broke"])

    wtf.main()

    assert recorded["text"] == "Something broke"


def test_main_handles_add_wtf_entry_error(monkeypatch, capsys):
    """If add_wtf_entry raises, main prints error and exits with code 1."""
    import src.wtf as wtf

    def boom(text: str) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(wtf, "add_wtf_entry", boom)
    monkeypatch.setattr(wtf.sys, "argv", ["wtf", "Something broke"])

    with pytest.raises(SystemExit) as exc:
        wtf.main()

    out = capsys.readouterr().out
    assert "Error adding entry: boom" in out
    assert exc.value.code == 1

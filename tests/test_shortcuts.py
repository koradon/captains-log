"""Tests for shortcut entry points (btw, wtf, wnext, stone standalone commands)."""

from typer.testing import CliRunner

from src.shortcuts import btw_app, stone_app, wnext_app, wtf_app

runner = CliRunner()


# -- btw shortcut -------------------------------------------------------------


class TestBtwShortcut:
    def test_btw_calls_add_manual_entry(self, monkeypatch):
        recorded = {}

        def fake_add(text):
            recorded["text"] = text

        monkeypatch.setattr("src.btw.add_manual_entry", fake_add)

        result = runner.invoke(btw_app, ["Did", "a", "thing"])
        assert result.exit_code == 0
        assert recorded["text"] == "Did a thing"

    def test_btw_single_arg_message(self, monkeypatch):
        recorded = {}
        monkeypatch.setattr(
            "src.btw.add_manual_entry", lambda t: recorded.update(text=t)
        )

        result = runner.invoke(btw_app, ["Did a thing"])
        assert result.exit_code == 0
        assert recorded["text"] == "Did a thing"

    def test_btw_version_flag(self):
        result = runner.invoke(btw_app, ["--version"])
        assert result.exit_code == 0
        assert "Captain's Log (btw) v" in result.output

    def test_btw_version_short_flag(self):
        result = runner.invoke(btw_app, ["-v"])
        assert result.exit_code == 0
        assert "Captain's Log (btw) v" in result.output

    def test_btw_help_flag(self):
        result = runner.invoke(btw_app, ["--help"])
        assert result.exit_code == 0
        assert "By The Way" in result.output

    def test_btw_empty_message_exits_with_error(self):
        result = runner.invoke(btw_app, ["   "])
        assert result.exit_code == 1
        assert "Entry text cannot be empty" in result.output

    def test_btw_no_args_shows_error(self):
        result = runner.invoke(btw_app, [])
        assert result.exit_code != 0

    def test_btw_with_log_level(self, monkeypatch):
        recorded = {}
        monkeypatch.setattr(
            "src.btw.add_manual_entry", lambda t: recorded.update(text=t)
        )

        result = runner.invoke(btw_app, ["--log-level", "debug", "hello"])
        assert result.exit_code == 0
        assert recorded["text"] == "hello"

    def test_btw_with_log_level_verbose(self, monkeypatch):
        recorded = {}
        monkeypatch.setattr(
            "src.btw.add_manual_entry", lambda t: recorded.update(text=t)
        )

        result = runner.invoke(btw_app, ["--log-level", "verbose", "hello"])
        assert result.exit_code == 0
        assert recorded["text"] == "hello"

    def test_btw_invalid_log_level(self):
        result = runner.invoke(btw_app, ["--log-level", "trace", "hello"])
        assert result.exit_code != 0

    def test_btw_business_logic_error(self, monkeypatch):
        def boom(text):
            raise RuntimeError("boom")

        monkeypatch.setattr("src.btw.add_manual_entry", boom)

        result = runner.invoke(btw_app, ["hello"])
        assert result.exit_code == 1
        assert "Error adding entry: boom" in result.output


# -- wtf shortcut -------------------------------------------------------------


class TestWtfShortcut:
    def test_wtf_calls_add_wtf_entry(self, monkeypatch):
        recorded = {}

        def fake_add(text):
            recorded["text"] = text

        monkeypatch.setattr("src.wtf.add_wtf_entry", fake_add)

        result = runner.invoke(wtf_app, ["Something", "broke"])
        assert result.exit_code == 0
        assert recorded["text"] == "Something broke"

    def test_wtf_single_arg_message(self, monkeypatch):
        recorded = {}
        monkeypatch.setattr("src.wtf.add_wtf_entry", lambda t: recorded.update(text=t))

        result = runner.invoke(wtf_app, ["Something broke"])
        assert result.exit_code == 0
        assert recorded["text"] == "Something broke"

    def test_wtf_version_flag(self):
        result = runner.invoke(wtf_app, ["--version"])
        assert result.exit_code == 0
        assert "Captain's Log (wtf) v" in result.output

    def test_wtf_version_short_flag(self):
        result = runner.invoke(wtf_app, ["-v"])
        assert result.exit_code == 0
        assert "Captain's Log (wtf) v" in result.output

    def test_wtf_help_flag(self):
        result = runner.invoke(wtf_app, ["--help"])
        assert result.exit_code == 0
        assert "What The Fault" in result.output

    def test_wtf_empty_message_exits_with_error(self):
        result = runner.invoke(wtf_app, ["   "])
        assert result.exit_code == 1
        assert "Entry text cannot be empty" in result.output

    def test_wtf_no_args_shows_error(self):
        result = runner.invoke(wtf_app, [])
        assert result.exit_code != 0

    def test_wtf_with_log_level(self, monkeypatch):
        recorded = {}
        monkeypatch.setattr("src.wtf.add_wtf_entry", lambda t: recorded.update(text=t))

        result = runner.invoke(wtf_app, ["--log-level", "debug", "hello"])
        assert result.exit_code == 0
        assert recorded["text"] == "hello"

    def test_wtf_invalid_log_level(self):
        result = runner.invoke(wtf_app, ["--log-level", "trace", "hello"])
        assert result.exit_code != 0

    def test_wtf_business_logic_error(self, monkeypatch):
        def boom(text):
            raise RuntimeError("boom")

        monkeypatch.setattr("src.wtf.add_wtf_entry", boom)

        result = runner.invoke(wtf_app, ["hello"])
        assert result.exit_code == 1
        assert "Error adding entry: boom" in result.output


# -- wnext shortcut -----------------------------------------------------------


class TestWnextShortcut:
    def test_wnext_calls_add_what_next_entry(self, monkeypatch):
        recorded = {}

        def fake_add(text, project_name, use_other):
            recorded["args"] = (text, project_name, use_other)

        monkeypatch.setattr("src.wnext.add_what_next_entry", fake_add)

        result = runner.invoke(wnext_app, ["Plan", "sprint"])
        assert result.exit_code == 0
        assert recorded["args"] == ("Plan sprint", None, False)

    def test_wnext_with_project_option(self, monkeypatch):
        recorded = {}

        def fake_add(text, project_name, use_other):
            recorded["args"] = (text, project_name, use_other)

        monkeypatch.setattr("src.wnext.add_what_next_entry", fake_add)

        result = runner.invoke(wnext_app, ["--project", "myproj", "Do", "it"])
        assert result.exit_code == 0
        assert recorded["args"] == ("Do it", "myproj", False)

    def test_wnext_with_project_short_option(self, monkeypatch):
        recorded = {}

        def fake_add(text, project_name, use_other):
            recorded["args"] = (text, project_name, use_other)

        monkeypatch.setattr("src.wnext.add_what_next_entry", fake_add)

        result = runner.invoke(wnext_app, ["-p", "myproj", "Do", "it"])
        assert result.exit_code == 0
        assert recorded["args"] == ("Do it", "myproj", False)

    def test_wnext_with_other_option(self, monkeypatch):
        recorded = {}

        def fake_add(text, project_name, use_other):
            recorded["args"] = (text, project_name, use_other)

        monkeypatch.setattr("src.wnext.add_what_next_entry", fake_add)

        result = runner.invoke(wnext_app, ["--other", "General", "thing"])
        assert result.exit_code == 0
        assert recorded["args"] == ("General thing", None, True)

    def test_wnext_with_other_short_option(self, monkeypatch):
        recorded = {}

        def fake_add(text, project_name, use_other):
            recorded["args"] = (text, project_name, use_other)

        monkeypatch.setattr("src.wnext.add_what_next_entry", fake_add)

        result = runner.invoke(wnext_app, ["-o", "General", "thing"])
        assert result.exit_code == 0
        assert recorded["args"] == ("General thing", None, True)

    def test_wnext_conflicting_flags_exits_with_error(self):
        result = runner.invoke(wnext_app, ["--project", "p", "--other", "some text"])
        assert result.exit_code == 1
        assert "cannot be used together" in result.output

    def test_wnext_empty_message_exits_with_error(self):
        result = runner.invoke(wnext_app, ["   "])
        assert result.exit_code == 1
        assert "Entry text cannot be empty" in result.output

    def test_wnext_no_args_shows_error(self):
        result = runner.invoke(wnext_app, [])
        assert result.exit_code != 0

    def test_wnext_version_flag(self):
        result = runner.invoke(wnext_app, ["--version"])
        assert result.exit_code == 0
        assert "Captain's Log (wnext) v" in result.output

    def test_wnext_version_short_flag(self):
        result = runner.invoke(wnext_app, ["-v"])
        assert result.exit_code == 0
        assert "Captain's Log (wnext) v" in result.output

    def test_wnext_help_flag(self):
        result = runner.invoke(wnext_app, ["--help"])
        assert result.exit_code == 0
        assert "Whats next" in result.output

    def test_wnext_with_log_level(self, monkeypatch):
        recorded = {}

        def fake_add(text, project_name, use_other):
            recorded["args"] = (text, project_name, use_other)

        monkeypatch.setattr("src.wnext.add_what_next_entry", fake_add)

        result = runner.invoke(wnext_app, ["--log-level", "debug", "hello"])
        assert result.exit_code == 0
        assert recorded["args"] == ("hello", None, False)

    def test_wnext_invalid_log_level(self):
        result = runner.invoke(wnext_app, ["--log-level", "trace", "hello"])
        assert result.exit_code != 0

    def test_wnext_business_logic_error(self, monkeypatch):
        def boom(text, project_name, use_other):
            raise RuntimeError("boom")

        monkeypatch.setattr("src.wnext.add_what_next_entry", boom)

        result = runner.invoke(wnext_app, ["hello"])
        assert result.exit_code == 1
        assert "Error adding What Next entry: boom" in result.output


# -- stone shortcut -----------------------------------------------------------


class TestStoneShortcut:
    def test_stone_calls_add_milestone_entry(self, monkeypatch):
        recorded = {}

        def fake_add(text):
            recorded["text"] = text

        monkeypatch.setattr("src.stone.add_milestone_entry", fake_add)

        result = runner.invoke(stone_app, ["Shipped", "v1.0"])
        assert result.exit_code == 0
        assert recorded["text"] == "Shipped v1.0"

    def test_stone_single_arg_message(self, monkeypatch):
        recorded = {}
        monkeypatch.setattr(
            "src.stone.add_milestone_entry", lambda t: recorded.update(text=t)
        )

        result = runner.invoke(stone_app, ["Shipped v1.0"])
        assert result.exit_code == 0
        assert recorded["text"] == "Shipped v1.0"

    def test_stone_version_flag(self):
        result = runner.invoke(stone_app, ["--version"])
        assert result.exit_code == 0
        assert "Captain's Log (stone) v" in result.output

    def test_stone_version_short_flag(self):
        result = runner.invoke(stone_app, ["-v"])
        assert result.exit_code == 0
        assert "Captain's Log (stone) v" in result.output

    def test_stone_help_flag(self):
        result = runner.invoke(stone_app, ["--help"])
        assert result.exit_code == 0
        assert "milestone" in result.output.lower()

    def test_stone_empty_message_exits_with_error(self):
        result = runner.invoke(stone_app, ["   "])
        assert result.exit_code == 1
        assert "Milestone text cannot be empty" in result.output

    def test_stone_no_args_shows_error(self):
        result = runner.invoke(stone_app, [])
        assert result.exit_code != 0

    def test_stone_with_log_level(self, monkeypatch):
        recorded = {}
        monkeypatch.setattr(
            "src.stone.add_milestone_entry", lambda t: recorded.update(text=t)
        )

        result = runner.invoke(stone_app, ["--log-level", "debug", "hello"])
        assert result.exit_code == 0
        assert recorded["text"] == "hello"

    def test_stone_invalid_log_level(self):
        result = runner.invoke(stone_app, ["--log-level", "trace", "hello"])
        assert result.exit_code != 0

    def test_stone_business_logic_error(self, monkeypatch):
        def boom(text):
            raise RuntimeError("boom")

        monkeypatch.setattr("src.stone.add_milestone_entry", boom)

        result = runner.invoke(stone_app, ["hello"])
        assert result.exit_code == 1
        assert "Error adding milestone entry: boom" in result.output

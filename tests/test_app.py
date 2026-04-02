"""Tests for the unified Typer CLI (captains-log command)."""

from typer.testing import CliRunner

from src.app import app

runner = CliRunner()


# -- version & help -----------------------------------------------------------


class TestVersionAndHelp:
    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "Captain's Log v" in result.output

    def test_version_short_flag(self):
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "Captain's Log v" in result.output

    def test_no_args_shows_help(self):
        result = runner.invoke(app, [])
        assert "Usage" in result.output or "captains-log" in result.output.lower()

    def test_help_flag_lists_subcommands(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "btw" in result.output
        assert "wtf" in result.output
        assert "wnext" in result.output
        assert "stone" in result.output
        assert "setup" in result.output
        assert "install-precommit-hooks" in result.output


# -- log level ----------------------------------------------------------------


class TestLogLevel:
    def test_valid_log_level_compact(self, monkeypatch):
        recorded = {}

        def spy(level):
            recorded["level"] = level

        monkeypatch.setattr("src.cli_logging.configure_log_level", spy)
        monkeypatch.setattr("src.btw.add_manual_entry", lambda t: None)

        result = runner.invoke(app, ["--log-level", "compact", "btw", "hello"])
        assert result.exit_code == 0
        assert recorded["level"] == "compact"

    def test_valid_log_level_verbose(self, monkeypatch):
        recorded = {}

        def spy(level):
            recorded["level"] = level

        monkeypatch.setattr("src.cli_logging.configure_log_level", spy)
        monkeypatch.setattr("src.btw.add_manual_entry", lambda t: None)

        result = runner.invoke(app, ["--log-level", "verbose", "btw", "hello"])
        assert result.exit_code == 0
        assert recorded["level"] == "verbose"

    def test_valid_log_level_debug(self, monkeypatch):
        recorded = {}

        def spy(level):
            recorded["level"] = level

        monkeypatch.setattr("src.cli_logging.configure_log_level", spy)
        monkeypatch.setattr("src.btw.add_manual_entry", lambda t: None)

        result = runner.invoke(app, ["--log-level", "debug", "btw", "hello"])
        assert result.exit_code == 0
        assert recorded["level"] == "debug"

    def test_invalid_log_level_exits_with_error(self):
        result = runner.invoke(app, ["--log-level", "trace", "btw", "hello"])
        assert result.exit_code != 0


# -- btw subcommand -----------------------------------------------------------


class TestBtwSubcommand:
    def test_btw_calls_add_manual_entry(self, monkeypatch):
        recorded = {}

        def fake_add(text):
            recorded["text"] = text

        monkeypatch.setattr("src.btw.add_manual_entry", fake_add)

        result = runner.invoke(app, ["btw", "Did", "a", "thing"])
        assert result.exit_code == 0
        assert recorded["text"] == "Did a thing"

    def test_btw_single_quoted_message(self, monkeypatch):
        recorded = {}
        monkeypatch.setattr(
            "src.btw.add_manual_entry", lambda t: recorded.update(text=t)
        )

        result = runner.invoke(app, ["btw", "Did a thing"])
        assert result.exit_code == 0
        assert recorded["text"] == "Did a thing"

    def test_btw_empty_message_exits_with_error(self):
        result = runner.invoke(app, ["btw", "   "])
        assert result.exit_code == 1
        assert "Entry text cannot be empty" in result.output

    def test_btw_no_args_shows_error(self):
        result = runner.invoke(app, ["btw"])
        assert result.exit_code != 0

    def test_btw_with_log_level(self, monkeypatch):
        recorded = {}
        monkeypatch.setattr(
            "src.btw.add_manual_entry", lambda t: recorded.update(text=t)
        )

        result = runner.invoke(app, ["--log-level", "debug", "btw", "hello"])
        assert result.exit_code == 0
        assert recorded["text"] == "hello"

    def test_btw_business_logic_error_exits_with_error(self, monkeypatch):
        def boom(text):
            raise RuntimeError("boom")

        monkeypatch.setattr("src.btw.add_manual_entry", boom)

        result = runner.invoke(app, ["btw", "hello"])
        assert result.exit_code == 1
        assert "Error adding entry: boom" in result.output

    def test_btw_help(self):
        result = runner.invoke(app, ["btw", "--help"])
        assert result.exit_code == 0
        assert "By The Way" in result.output


# -- wtf subcommand -----------------------------------------------------------


class TestWtfSubcommand:
    def test_wtf_calls_add_wtf_entry(self, monkeypatch):
        recorded = {}

        def fake_add(text):
            recorded["text"] = text

        monkeypatch.setattr("src.wtf.add_wtf_entry", fake_add)

        result = runner.invoke(app, ["wtf", "Something", "broke"])
        assert result.exit_code == 0
        assert recorded["text"] == "Something broke"

    def test_wtf_single_quoted_message(self, monkeypatch):
        recorded = {}
        monkeypatch.setattr("src.wtf.add_wtf_entry", lambda t: recorded.update(text=t))

        result = runner.invoke(app, ["wtf", "Something broke"])
        assert result.exit_code == 0
        assert recorded["text"] == "Something broke"

    def test_wtf_empty_message_exits_with_error(self):
        result = runner.invoke(app, ["wtf", "   "])
        assert result.exit_code == 1
        assert "Entry text cannot be empty" in result.output

    def test_wtf_no_args_shows_error(self):
        result = runner.invoke(app, ["wtf"])
        assert result.exit_code != 0

    def test_wtf_business_logic_error_exits_with_error(self, monkeypatch):
        def boom(text):
            raise RuntimeError("boom")

        monkeypatch.setattr("src.wtf.add_wtf_entry", boom)

        result = runner.invoke(app, ["wtf", "hello"])
        assert result.exit_code == 1
        assert "Error adding entry: boom" in result.output

    def test_wtf_help(self):
        result = runner.invoke(app, ["wtf", "--help"])
        assert result.exit_code == 0
        assert "What The Fault" in result.output


# -- wnext subcommand ---------------------------------------------------------


class TestWnextSubcommand:
    def test_wnext_calls_add_what_next_entry(self, monkeypatch):
        recorded = {}

        def fake_add(text, project_name, use_other):
            recorded["args"] = (text, project_name, use_other)

        monkeypatch.setattr("src.wnext.add_what_next_entry", fake_add)

        result = runner.invoke(app, ["wnext", "Plan", "sprint"])
        assert result.exit_code == 0
        assert recorded["args"] == ("Plan sprint", None, False)

    def test_wnext_with_project_option(self, monkeypatch):
        recorded = {}

        def fake_add(text, project_name, use_other):
            recorded["args"] = (text, project_name, use_other)

        monkeypatch.setattr("src.wnext.add_what_next_entry", fake_add)

        result = runner.invoke(app, ["wnext", "--project", "myproj", "Do", "it"])
        assert result.exit_code == 0
        assert recorded["args"] == ("Do it", "myproj", False)

    def test_wnext_with_project_short_option(self, monkeypatch):
        recorded = {}

        def fake_add(text, project_name, use_other):
            recorded["args"] = (text, project_name, use_other)

        monkeypatch.setattr("src.wnext.add_what_next_entry", fake_add)

        result = runner.invoke(app, ["wnext", "-p", "myproj", "Do", "it"])
        assert result.exit_code == 0
        assert recorded["args"] == ("Do it", "myproj", False)

    def test_wnext_with_other_option(self, monkeypatch):
        recorded = {}

        def fake_add(text, project_name, use_other):
            recorded["args"] = (text, project_name, use_other)

        monkeypatch.setattr("src.wnext.add_what_next_entry", fake_add)

        result = runner.invoke(app, ["wnext", "--other", "General", "thing"])
        assert result.exit_code == 0
        assert recorded["args"] == ("General thing", None, True)

    def test_wnext_with_other_short_option(self, monkeypatch):
        recorded = {}

        def fake_add(text, project_name, use_other):
            recorded["args"] = (text, project_name, use_other)

        monkeypatch.setattr("src.wnext.add_what_next_entry", fake_add)

        result = runner.invoke(app, ["wnext", "-o", "General", "thing"])
        assert result.exit_code == 0
        assert recorded["args"] == ("General thing", None, True)

    def test_wnext_conflicting_flags_exits_with_error(self):
        result = runner.invoke(app, ["wnext", "--project", "p", "--other", "some text"])
        assert result.exit_code == 1
        assert "cannot be used together" in result.output

    def test_wnext_empty_message_exits_with_error(self):
        result = runner.invoke(app, ["wnext", "   "])
        assert result.exit_code == 1
        assert "Entry text cannot be empty" in result.output

    def test_wnext_no_args_shows_error(self):
        result = runner.invoke(app, ["wnext"])
        assert result.exit_code != 0

    def test_wnext_business_logic_error_exits_with_error(self, monkeypatch):
        def boom(text, project_name, use_other):
            raise RuntimeError("boom")

        monkeypatch.setattr("src.wnext.add_what_next_entry", boom)

        result = runner.invoke(app, ["wnext", "hello"])
        assert result.exit_code == 1
        assert "Error adding What Next entry: boom" in result.output

    def test_wnext_help(self):
        result = runner.invoke(app, ["wnext", "--help"])
        assert result.exit_code == 0
        assert "Whats next" in result.output


# -- stone subcommand ---------------------------------------------------------


class TestStoneSubcommand:
    def test_stone_calls_add_milestone_entry(self, monkeypatch):
        recorded = {}

        def fake_add(text):
            recorded["text"] = text

        monkeypatch.setattr("src.stone.add_milestone_entry", fake_add)

        result = runner.invoke(app, ["stone", "Shipped", "v1.0"])
        assert result.exit_code == 0
        assert recorded["text"] == "Shipped v1.0"

    def test_stone_single_quoted_message(self, monkeypatch):
        recorded = {}
        monkeypatch.setattr(
            "src.stone.add_milestone_entry", lambda t: recorded.update(text=t)
        )

        result = runner.invoke(app, ["stone", "Shipped v1.0"])
        assert result.exit_code == 0
        assert recorded["text"] == "Shipped v1.0"

    def test_stone_empty_message_exits_with_error(self):
        result = runner.invoke(app, ["stone", "   "])
        assert result.exit_code == 1
        assert "Milestone text cannot be empty" in result.output

    def test_stone_no_args_shows_error(self):
        result = runner.invoke(app, ["stone"])
        assert result.exit_code != 0

    def test_stone_business_logic_error_exits_with_error(self, monkeypatch):
        def boom(text):
            raise RuntimeError("boom")

        monkeypatch.setattr("src.stone.add_milestone_entry", boom)

        result = runner.invoke(app, ["stone", "hello"])
        assert result.exit_code == 1
        assert "Error adding milestone entry: boom" in result.output

    def test_stone_help(self):
        result = runner.invoke(app, ["stone", "--help"])
        assert result.exit_code == 0
        assert "milestone" in result.output.lower()


# -- setup & install-precommit-hooks ------------------------------------------


class TestSetupSubcommands:
    def test_setup_calls_cli_setup(self, monkeypatch):
        called = {"setup": False}

        def fake_setup():
            called["setup"] = True

        monkeypatch.setattr("src.cli.setup", fake_setup)

        result = runner.invoke(app, ["setup"])
        assert result.exit_code == 0
        assert called["setup"] is True

    def test_install_precommit_hooks_calls_cli(self, monkeypatch):
        called = {"install": False}

        def fake_install():
            called["install"] = True

        monkeypatch.setattr("src.cli.install_precommit_hooks", fake_install)

        result = runner.invoke(app, ["install-precommit-hooks"])
        assert result.exit_code == 0
        assert called["install"] is True

    def test_setup_help(self):
        result = runner.invoke(app, ["setup", "--help"])
        assert result.exit_code == 0
        assert "Set up" in result.output

    def test_install_precommit_hooks_help(self):
        result = runner.invoke(app, ["install-precommit-hooks", "--help"])
        assert result.exit_code == 0
        assert "pre-commit" in result.output.lower()

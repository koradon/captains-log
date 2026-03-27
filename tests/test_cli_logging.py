"""Tests for shared CLI logging helpers."""

import pytest

from src import cli_logging


def test_split_log_level_args_defaults_to_compact():
    args, level = cli_logging.split_log_level_args(["hello", "world"])
    assert args == ["hello", "world"]
    assert level == "compact"


def test_split_log_level_args_accepts_separate_value():
    args, level = cli_logging.split_log_level_args(
        ["--log-level", "debug", "do", "thing"]
    )
    assert args == ["do", "thing"]
    assert level == "debug"


def test_split_log_level_args_accepts_equals_form():
    args, level = cli_logging.split_log_level_args(
        ["--log-level=verbose", "do", "thing"]
    )
    assert args == ["do", "thing"]
    assert level == "verbose"


def test_split_log_level_args_last_wins():
    args, level = cli_logging.split_log_level_args(
        ["--log-level=verbose", "--log-level", "debug", "do", "thing"]
    )
    assert args == ["do", "thing"]
    assert level == "debug"


def test_split_log_level_args_rejects_missing_value():
    with pytest.raises(ValueError) as exc:
        cli_logging.split_log_level_args(["--log-level"])
    assert "--log-level requires a value" in str(exc.value)


def test_split_log_level_args_rejects_invalid_value():
    with pytest.raises(ValueError) as exc:
        cli_logging.split_log_level_args(["--log-level", "trace"])
    assert "invalid --log-level value" in str(exc.value)


def test_verbose_and_debug_helpers_respect_levels(capsys):
    cli_logging.configure_log_level("compact")
    cli_logging.verbose("v1")
    cli_logging.debug("d1")
    assert capsys.readouterr().out == ""

    cli_logging.configure_log_level("verbose")
    cli_logging.verbose("v2")
    out = capsys.readouterr().out
    assert "v2" in out

    cli_logging.debug("d2")
    assert capsys.readouterr().out == ""

    cli_logging.configure_log_level("debug")
    cli_logging.debug("d3")
    out = capsys.readouterr().out
    assert "d3" in out


def test_compact_mode_keeps_plain_output(capsys):
    cli_logging.configure_log_level("compact")
    cli_logging.success("ok")
    out = capsys.readouterr().out.strip()
    assert out == "ok"

"""Shortcut entry points for standalone commands (btw, wtf, wnext, stone).

Each command has its own Typer app so it can be invoked directly
(e.g. ``btw "some text"``) without a subcommand name.
"""

from typing import List, Optional

import typer

from src import cli_logging
from src.cli_logging import LogLevel


def _make_version_callback(cmd_name: str):
    """Create a --version callback that prints the command-specific banner."""

    def _callback(value: bool) -> None:
        if value:
            from src import __version__

            print(f"Captain's Log ({cmd_name}) v{__version__}")
            raise typer.Exit()

    return _callback


# ---------------------------------------------------------------------------
# btw
# ---------------------------------------------------------------------------

btw_app = typer.Typer(add_completion=False)


@btw_app.command(help="Add manual log entries (By The Way).")
def _btw_cmd(
    message: List[str] = typer.Argument(..., help="What you have done."),
    log_level: LogLevel = typer.Option(
        LogLevel.compact, "--log-level", help="Logging verbosity."
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=_make_version_callback("btw"),
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    cli_logging.configure_log_level(log_level.value)
    text = " ".join(message).strip()
    if not text:
        cli_logging.error("Entry text cannot be empty")
        raise typer.Exit(code=1)
    try:
        from src.btw import add_manual_entry

        add_manual_entry(text)
    except SystemExit:
        raise
    except Exception as e:
        cli_logging.error(f"Error adding entry: {e}")
        raise typer.Exit(code=1) from None


def btw_main() -> None:
    """Entry point for the ``btw`` shortcut command."""
    btw_app()


# ---------------------------------------------------------------------------
# wtf
# ---------------------------------------------------------------------------

wtf_app = typer.Typer(add_completion=False)


@wtf_app.command(help="Add issue entries (What The Fault).")
def _wtf_cmd(
    message: List[str] = typer.Argument(..., help="What broke or got weird."),
    log_level: LogLevel = typer.Option(
        LogLevel.compact, "--log-level", help="Logging verbosity."
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=_make_version_callback("wtf"),
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    cli_logging.configure_log_level(log_level.value)
    text = " ".join(message).strip()
    if not text:
        cli_logging.error("Entry text cannot be empty")
        raise typer.Exit(code=1)
    try:
        from src.wtf import add_wtf_entry

        add_wtf_entry(text)
    except SystemExit:
        raise
    except Exception as e:
        cli_logging.error(f"Error adding entry: {e}")
        raise typer.Exit(code=1) from None


def wtf_main() -> None:
    """Entry point for the ``wtf`` shortcut command."""
    wtf_app()


# ---------------------------------------------------------------------------
# wnext
# ---------------------------------------------------------------------------

wnext_app = typer.Typer(add_completion=False)


@wnext_app.command(help="Add entries to 'Whats next' section.")
def _wnext_cmd(
    message: List[str] = typer.Argument(..., help="What to do next."),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Target project name."
    ),
    other: bool = typer.Option(False, "--other", "-o", help="Use 'other' subsection."),
    log_level: LogLevel = typer.Option(
        LogLevel.compact, "--log-level", help="Logging verbosity."
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=_make_version_callback("wnext"),
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    cli_logging.configure_log_level(log_level.value)
    if project is not None and other:
        cli_logging.error("--project/-p and --other/-o cannot be used together")
        raise typer.Exit(code=1)
    text = " ".join(message).strip()
    if not text:
        cli_logging.error("Entry text cannot be empty")
        raise typer.Exit(code=1)
    try:
        from src.wnext import add_what_next_entry

        add_what_next_entry(text, project, other)
    except SystemExit:
        raise
    except Exception as e:
        cli_logging.error(f"Error adding What Next entry: {e}")
        raise typer.Exit(code=1) from None


def wnext_main() -> None:
    """Entry point for the ``wnext`` shortcut command."""
    wnext_app()


# ---------------------------------------------------------------------------
# stone
# ---------------------------------------------------------------------------

stone_app = typer.Typer(add_completion=False)


@stone_app.command(help="Add entries to yearly milestones file.")
def _stone_cmd(
    message: List[str] = typer.Argument(..., help="Describe the milestone."),
    log_level: LogLevel = typer.Option(
        LogLevel.compact, "--log-level", help="Logging verbosity."
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=_make_version_callback("stone"),
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    cli_logging.configure_log_level(log_level.value)
    text = " ".join(message).strip()
    if not text:
        cli_logging.error("Milestone text cannot be empty")
        raise typer.Exit(code=1)
    try:
        from src.stone import add_milestone_entry

        add_milestone_entry(text)
    except SystemExit:
        raise
    except Exception as e:
        cli_logging.error(f"Error adding milestone entry: {e}")
        raise typer.Exit(code=1) from None


def stone_main() -> None:
    """Entry point for the ``stone`` shortcut command."""
    stone_app()

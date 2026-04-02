"""Unified Typer CLI for Captain's Log.

Provides the ``captains-log`` command with subcommands for every tool.
"""

from typing import List, Optional

import typer

from src import __version__, cli_logging
from src.cli_logging import LogLevel


def _version_callback(value: bool) -> None:
    if value:
        print(f"Captain's Log v{__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="captains-log",
    help="Captain's Log - Automatically log your git commits.",
    add_completion=False,
    no_args_is_help=True,
)


@app.callback()
def _app_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
    log_level: LogLevel = typer.Option(
        LogLevel.compact,
        "--log-level",
        help="Logging verbosity.",
    ),
) -> None:
    """Captain's Log - Automatically log your git commits."""
    cli_logging.configure_log_level(log_level.value)


@app.command()
def btw(
    message: List[str] = typer.Argument(..., help="What you have done."),
) -> None:
    """Add manual log entries (By The Way)."""
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


@app.command()
def wtf(
    message: List[str] = typer.Argument(..., help="What broke or got weird."),
) -> None:
    """Add issue entries (What The Fault)."""
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


@app.command()
def wnext(
    message: List[str] = typer.Argument(..., help="What to do next."),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Target project name."
    ),
    other: bool = typer.Option(False, "--other", "-o", help="Use 'other' subsection."),
) -> None:
    """Add entries to 'Whats next' section."""
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


@app.command()
def stone(
    message: List[str] = typer.Argument(..., help="Describe the milestone."),
) -> None:
    """Add entries to yearly milestones file."""
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


@app.command()
def setup() -> None:
    """Set up Captain's Log for the first time."""
    from src.cli import setup as _setup

    _setup()


@app.command(name="install-precommit-hooks")
def install_precommit_hooks() -> None:
    """Install global pre-commit wrapper hooks."""
    from src.cli import install_precommit_hooks as _install

    _install()


def main() -> None:
    """Entry point for the ``captains-log`` command."""
    app()

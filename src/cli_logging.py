"""Shared CLI logging helpers for Captain's Log commands."""

from __future__ import annotations

import os
import sys
from typing import Sequence

LOG_LEVELS = ("compact", "verbose", "debug")
DEFAULT_LOG_LEVEL = "compact"
_current_log_level = DEFAULT_LOG_LEVEL


def configure_log_level(level: str) -> None:
    """Set the process-wide CLI logging level."""
    global _current_log_level
    _current_log_level = level


def get_log_level() -> str:
    """Get the active process-wide CLI logging level."""
    return _current_log_level


def is_verbose() -> bool:
    """Return True when verbose output should be shown."""
    return _current_log_level in ("verbose", "debug")


def is_debug() -> bool:
    """Return True when debug output should be shown."""
    return _current_log_level == "debug"


def split_log_level_args(argv: Sequence[str]) -> tuple[list[str], str]:
    """Extract --log-level from argv and return cleaned args + selected level."""
    cleaned: list[str] = []
    selected = DEFAULT_LOG_LEVEL
    i = 0

    while i < len(argv):
        arg = argv[i]

        if arg == "--log-level":
            i += 1
            if i >= len(argv):
                raise ValueError(
                    "Error: --log-level requires a value (compact, verbose, debug)"
                )
            selected = argv[i].strip().lower()
        elif arg.startswith("--log-level="):
            selected = arg.split("=", 1)[1].strip().lower()
        else:
            cleaned.append(arg)
        i += 1

    if selected not in LOG_LEVELS:
        raise ValueError(
            "Error: invalid --log-level value "
            f"'{selected}'. Allowed values: compact, verbose, debug"
        )

    return cleaned, selected


def _supports_color() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _use_emoji() -> bool:
    return not os.getenv("CAPTAINS_LOG_NO_EMOJI")


def _decorate(message: str, kind: str) -> str:
    color = ""
    reset = ""
    emoji = ""

    if _supports_color():
        color = {
            "success": "\033[32m",
            "warning": "\033[33m",
            "error": "\033[31m",
            "info": "\033[36m",
            "debug": "\033[90m",
        }.get(kind, "")
        reset = "\033[0m" if color else ""

    if _use_emoji():
        emoji = {
            "success": "✅ ",
            "warning": "⚠️ ",
            "error": "❌ ",
            "info": "ℹ️ ",
            "debug": "🛠️ ",
        }.get(kind, "")

    # Keep compact mode conservative: no extra decoration by default.
    if _current_log_level == "compact":
        return message

    return f"{color}{emoji}{message}{reset}"


def info(message: str) -> None:
    print(_decorate(message, "info"))


def success(message: str) -> None:
    print(_decorate(message, "success"))


def warning(message: str) -> None:
    print(_decorate(message, "warning"))


def error(message: str) -> None:
    print(_decorate(message, "error"))


def verbose(message: str) -> None:
    if is_verbose():
        print(_decorate(message, "info"))


def debug(message: str) -> None:
    if is_debug():
        print(_decorate(message, "debug"))

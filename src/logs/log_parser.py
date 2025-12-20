"""Log file parsing functionality for Captain's Log."""

from enum import Enum
from pathlib import Path

from src.logs.log_models import LogData


class Section(Enum):
    """Log file sections with their headers."""

    WHAT_I_DID = "What I did"
    WHAT_BROKE = "What Broke or Got Weird"


class LogParser:
    """Handles parsing of markdown log files."""

    @staticmethod
    def parse_log_file(file_path: Path) -> LogData:
        """Parse a markdown log file into structured data.

        Args:
            file_path: Path to the log file

        Returns:
            LogData containing the parsed information
        """
        if not file_path.exists():
            return LogData()

        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read log file {file_path}: {e}")
            return LogData()

        return LogParser.parse_log_content(content)

    @staticmethod
    def parse_log_content(content: str) -> LogData:
        """Parse log content from a string.

        Args:
            content: Log file content as string

        Returns:
            LogData containing the parsed information
        """
        lines = content.splitlines()
        repos = {}
        what_broke = []
        current_section = None
        current_repo = None

        for line in lines:
            line_stripped = line.strip()

            # Check for section headers
            if line_stripped.startswith("# "):
                if Section.WHAT_BROKE.value in line_stripped:
                    current_section = Section.WHAT_BROKE
                elif Section.WHAT_I_DID.value in line_stripped:
                    current_section = Section.WHAT_I_DID
                else:
                    current_section = None  # Other sections, ignore
                current_repo = None
                continue

            # Handle repository headers (## repo-name)
            if (
                line_stripped.startswith("## ")
                and current_section == Section.WHAT_I_DID
            ):
                current_repo = line_stripped[3:].strip()
                if current_repo:
                    repos[current_repo] = []
                continue

            # Handle entry lines (- entry text)
            if line_stripped.startswith("- ") and line_stripped:
                if current_section == Section.WHAT_BROKE:
                    what_broke.append(line_stripped)
                elif current_section == Section.WHAT_I_DID and current_repo:
                    repos[current_repo].append(line_stripped)

        return LogData(repos=repos, what_broke=what_broke)

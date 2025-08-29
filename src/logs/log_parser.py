"""Log file parsing functionality for Captain's Log."""

from pathlib import Path

from logs.log_models import LogData


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
            content = file_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read log file {file_path}: {e}")
            return LogData()

        repos = {}
        current_repo = None

        for line in content:
            line = line.strip()

            if line.startswith("## "):
                # Repository section header
                current_repo = line[3:].strip()
                if current_repo:  # Only add non-empty repo names
                    repos[current_repo] = []
            elif current_repo and line.startswith("- ") and line.strip():
                # Entry line under a repository
                repos[current_repo].append(line.strip())

        return LogData(repos=repos)

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
        current_repo = None

        for line in lines:
            line = line.strip()

            if line.startswith("## "):
                # Repository section header
                current_repo = line[3:].strip()
                if current_repo:  # Only add non-empty repo names
                    repos[current_repo] = []
            elif current_repo and line.startswith("- ") and line.strip():
                # Entry line under a repository
                repos[current_repo].append(line.strip())

        return LogData(repos=repos)

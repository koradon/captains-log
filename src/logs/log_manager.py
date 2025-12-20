"""Log management functionality for Captain's Log."""

import re
from datetime import date
from pathlib import Path
from typing import Optional

from src.config.config_models import Config
from src.logs.log_models import LogData, LogFileInfo
from src.logs.log_parser import LogParser
from src.logs.log_writer import LogWriter
from src.projects.project_models import ProjectInfo


class LogManager:
    """High-level log management operations."""

    BASE_DIR = Path.home() / ".captains-log" / "projects"
    LOG_FILE_PATTERN = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2})\.md$")

    def __init__(self, config: Config):
        """Initialize with configuration.

        Args:
            config: Application configuration
        """
        self.config = config
        self.parser = LogParser()
        self._last_organized_month = None

    def get_log_file_info(
        self, project: ProjectInfo, log_date: Optional[date] = None
    ) -> LogFileInfo:
        """Get log file information for a project.

        Args:
            project: Project information
            log_date: Date for the log file (defaults to today)

        Returns:
            LogFileInfo with file path and repository information
        """
        if log_date is None:
            log_date = date.today()

        log_file_name = f"{log_date.year}.{log_date.month:02d}.{log_date.day:02d}.md"
        log_repo_path = project.log_repo or self.config.global_log_repo

        # Organize old files if needed
        if self._should_organize_files(log_date, project, log_repo_path):
            self._organize_old_log_files(project, log_repo_path)
            self._last_organized_month = (date.today().year, date.today().month)

        # Build the file path
        base_dir = self._get_base_directory(project, log_repo_path)
        log_file_path = self._build_log_file_path(base_dir, log_file_name, log_date)

        # Resolve log_repo_path if it exists
        resolved_log_repo_path = log_repo_path.resolve() if log_repo_path else None

        return LogFileInfo(
            file_path=log_file_path,
            log_repo_path=resolved_log_repo_path,
            project_name=project.name,
            date_created=log_date,
        )

    def load_log(self, log_info: LogFileInfo) -> LogData:
        """Load log data from file.

        Args:
            log_info: Log file information

        Returns:
            LogData containing the parsed log
        """
        # Try the expected path first
        if log_info.file_path.exists():
            return self.parser.parse_log_file(log_info.file_path)

        # Fallback: if loading a past month log and file doesn't exist in year/month dir,
        # check if it's still in the base directory (hasn't been organized yet)
        if not self._is_current_month(log_info.date_created):
            base_dir = self._get_base_directory_from_log_info(log_info)
            fallback_path = base_dir / log_info.file_path.name
            if fallback_path.exists():
                return self.parser.parse_log_file(fallback_path)

        # File doesn't exist in either location, return empty log
        return self.parser.parse_log_file(log_info.file_path)

    def save_log(self, log_info: LogFileInfo, log_data: LogData):
        """Save log data to file.

        Args:
            log_info: Log file information
            log_data: Log data to save
        """
        writer = LogWriter()
        writer.write_log_file(log_info.file_path, log_data)

    def _is_current_month(self, log_date: date) -> bool:
        """Check if the given date is in the current month.

        Args:
            log_date: Date to check

        Returns:
            True if the date is in the current month, False otherwise
        """
        today = date.today()
        return log_date.year == today.year and log_date.month == today.month

    def _get_base_directory(
        self, project: ProjectInfo, log_repo_path: Optional[Path] = None
    ) -> Path:
        """Get the base directory where log files are stored for a project.

        Args:
            project: Project information
            log_repo_path: Optional log repository path (for git repos)

        Returns:
            Path to the base directory
        """
        if log_repo_path is None:
            return self.BASE_DIR / project.name

        log_repo_path = log_repo_path.resolve()
        if log_repo_path == self.config.global_log_repo:
            return log_repo_path / project.name
        else:
            return log_repo_path

    def _get_base_directory_from_log_info(self, log_info: LogFileInfo) -> Path:
        """Get the base directory from LogFileInfo.

        Args:
            log_info: Log file information

        Returns:
            Path to the base directory
        """
        if log_info.log_repo_path is None:
            return self.BASE_DIR / log_info.project_name

        if log_info.log_repo_path == self.config.global_log_repo:
            return log_info.log_repo_path / log_info.project_name
        else:
            return log_info.log_repo_path

    def _build_log_file_path(
        self, base_dir: Path, log_file_name: str, log_date: date
    ) -> Path:
        """Build the full path to a log file.

        Args:
            base_dir: Base directory for log files
            log_file_name: Name of the log file
            log_date: Date of the log file

        Returns:
            Full path to the log file
        """
        if self._is_current_month(log_date):
            return base_dir / log_file_name
        else:
            return (
                base_dir / str(log_date.year) / f"{log_date.month:02d}" / log_file_name
            )

    def _should_organize_files(
        self, log_date: date, project: ProjectInfo, log_repo_path: Optional[Path] = None
    ) -> bool:
        """Determine if old log files should be organized.

        Args:
            log_date: Date of the log being accessed
            project: Project information
            log_repo_path: Optional log repository path

        Returns:
            True if files should be organized, False otherwise
        """
        today = date.today()
        current_month = (today.year, today.month)

        if self._is_current_month(log_date):
            # When accessing current month, organize if it's a new month
            return (
                self._last_organized_month is None
                or self._last_organized_month != current_month
            )
        else:
            # When accessing past month logs, check if there are old files to organize
            if self._last_organized_month is None:
                return self._has_old_files_in_main_directory(project, log_repo_path)
            return False

    def _has_old_files_in_main_directory(
        self, project: ProjectInfo, log_repo_path: Optional[Path] = None
    ) -> bool:
        """Check if there are any old log files in the main directory that need organizing.

        Args:
            project: Project information
            log_repo_path: Optional log repository path (for git repos)

        Returns:
            True if there are old files in the main directory, False otherwise
        """
        base_dir = self._get_base_directory(project, log_repo_path)
        if not base_dir.exists():
            return False

        today = date.today()
        current_year = today.year
        current_month = today.month

        for file_path in base_dir.iterdir():
            if not file_path.is_file():
                continue

            match = self.LOG_FILE_PATTERN.match(file_path.name)
            if match:
                file_year = int(match.group(1))
                file_month = int(match.group(2))

                if file_year != current_year or file_month != current_month:
                    return True

        return False

    def _find_old_log_files(self, base_dir: Path) -> list[tuple[Path, int, int]]:
        """Find all old log files in the base directory that need to be moved.

        Args:
            base_dir: Base directory to search

        Returns:
            List of tuples (file_path, year, month) for files to move
        """
        if not base_dir.exists():
            return []

        today = date.today()
        current_year = today.year
        current_month = today.month

        files_to_move = []
        for file_path in base_dir.iterdir():
            if not file_path.is_file():
                continue

            match = self.LOG_FILE_PATTERN.match(file_path.name)
            if match:
                file_year = int(match.group(1))
                file_month = int(match.group(2))

                if file_year != current_year or file_month != current_month:
                    files_to_move.append((file_path, file_year, file_month))

        return files_to_move

    def _move_log_file_to_year_month(
        self, file_path: Path, file_year: int, file_month: int, base_dir: Path
    ):
        """Move a log file to its year/month subdirectory.

        Args:
            file_path: Path to the file to move
            file_year: Year of the log file
            file_month: Month of the log file
            base_dir: Base directory for log files
        """
        target_dir = base_dir / str(file_year) / f"{file_month:02d}"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / file_path.name

        if not target_path.exists():
            try:
                file_path.rename(target_path)
            except (OSError, PermissionError) as e:
                print(f"Warning: Could not move {file_path} to {target_path}: {e}")

    def _organize_old_log_files(
        self, project: ProjectInfo, log_repo_path: Optional[Path] = None
    ):
        """Organize old log files into year/month directories.

        Moves all log files from previous months to year/month subdirectories.
        Only files from the current month remain in the main directory.

        Args:
            project: Project information
            log_repo_path: Optional log repository path (for git repos)
        """
        base_dir = self._get_base_directory(project, log_repo_path)
        files_to_move = self._find_old_log_files(base_dir)

        for file_path, file_year, file_month in files_to_move:
            self._move_log_file_to_year_month(
                file_path, file_year, file_month, base_dir
            )

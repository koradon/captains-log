"""Log management functionality for Captain's Log."""

from datetime import date
from pathlib import Path

from src.config.config_models import Config
from src.logs.log_models import LogData, LogFileInfo
from src.logs.log_parser import LogParser
from src.logs.log_writer import LogWriter
from src.projects.project_models import ProjectInfo


class LogManager:
    """High-level log management operations."""

    BASE_DIR = Path.home() / ".captains-log" / "projects"

    def __init__(self, config: Config):
        """Initialize with configuration.

        Args:
            config: Application configuration
        """
        self.config = config
        self.parser = LogParser()

    def get_log_file_info(
        self, project: ProjectInfo, log_date: date = None
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

        # Determine log repository and file path
        log_repo_path = project.log_repo or self.config.global_log_repo

        if log_repo_path is None:
            # No git repository configured, use local storage
            log_file_path = self.BASE_DIR / project.name / log_file_name
            return LogFileInfo(
                file_path=log_file_path,
                log_repo_path=None,
                project_name=project.name,
                date_created=log_date,
            )

        # Git repository configured
        log_repo_path = log_repo_path.resolve()

        if log_repo_path == self.config.global_log_repo:
            # Global repository: project subdirectory
            log_file_path = log_repo_path / project.name / log_file_name
        else:
            # Project-specific repository: root level
            log_file_path = log_repo_path / log_file_name

        return LogFileInfo(
            file_path=log_file_path,
            log_repo_path=log_repo_path,
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
        return self.parser.parse_log_file(log_info.file_path)

    def save_log(self, log_info: LogFileInfo, log_data: LogData):
        """Save log data to file.

        Args:
            log_info: Log file information
            log_data: Log data to save
        """
        writer = LogWriter()
        writer.write_log_file(log_info.file_path, log_data)

"""Log-related data models for Captain's Log."""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class LogData:
    """Represents the structured data of a log file."""

    repos: Dict[str, List[str]] = field(default_factory=dict)
    what_broke: List[str] = field(default_factory=list)

    def get_repo_entries(self, repo_name: str) -> List[str]:
        """Get entries for a specific repository."""
        return self.repos.get(repo_name, [])

    def set_repo_entries(self, repo_name: str, entries: List[str]):
        """Set entries for a specific repository."""
        self.repos[repo_name] = entries

    def add_repo_entry(self, repo_name: str, entry: str):
        """Add a single entry to a repository."""
        if repo_name not in self.repos:
            self.repos[repo_name] = []
        self.repos[repo_name].append(entry)

    def has_repo(self, repo_name: str) -> bool:
        """Check if a repository exists in the log data."""
        return repo_name in self.repos

    def get_what_broke_entries(self) -> List[str]:
        """Get all entries from the 'What Broke or Got Weird' section."""
        return self.what_broke

    def add_what_broke_entry(self, entry: str):
        """Add an entry to the 'What Broke or Got Weird' section."""
        if entry not in self.what_broke:
            self.what_broke.append(entry)


@dataclass
class LogFileInfo:
    """Information about a log file and its location."""

    file_path: Path
    log_repo_path: Optional[Path]
    project_name: str
    date_created: date

    @property
    def file_name(self) -> str:
        """Get the log file name."""
        return self.file_path.name

    @property
    def exists(self) -> bool:
        """Check if the log file exists."""
        return self.file_path.exists()

    @property
    def has_git_repo(self) -> bool:
        """Check if this log is in a git repository."""
        return self.log_repo_path is not None

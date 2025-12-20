"""Project-related data models for Captain's Log."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.config.config_models import ProjectConfig


@dataclass
class ProjectInfo:
    """Information about a discovered project."""

    name: str
    config: ProjectConfig
    base_dir: Path

    @property
    def log_repo(self) -> Optional[Path]:
        """Get the log repository path for this project."""
        return self.config.log_repo

    @property
    def root_dir(self) -> Optional[Path]:
        """Get the root directory for this project."""
        return self.config.root

"""Configuration data models for Captain's Log."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Union


@dataclass
class ProjectConfig:
    """Configuration for a single project."""

    root: Optional[Path] = None
    log_repo: Optional[Path] = None

    @classmethod
    def from_dict(cls, data: Union[str, Dict]) -> "ProjectConfig":
        """Create ProjectConfig from dictionary or string."""
        if isinstance(data, str):
            # Simple string format: just the root path
            return cls(root=Path(data).resolve() if data else None)
        elif isinstance(data, dict):
            # Dictionary format with explicit fields
            root = data.get("root")
            log_repo = data.get("log_repo")
            return cls(
                root=Path(root).resolve() if root else None,
                log_repo=Path(log_repo).resolve() if log_repo else None,
            )
        else:
            return cls()


@dataclass
class Config:
    """Main configuration for Captain's Log."""

    global_log_repo: Optional[Path] = None
    projects: Dict[str, ProjectConfig] = None

    def __post_init__(self):
        """Initialize empty projects dict if None."""
        if self.projects is None:
            self.projects = {}

    @classmethod
    def from_dict(cls, data: Dict) -> "Config":
        """Create Config from dictionary."""
        global_log_repo = data.get("global_log_repo")
        projects_data = data.get("projects", {})

        # Convert projects data to ProjectConfig objects
        projects = {}
        for name, project_data in projects_data.items():
            projects[name] = ProjectConfig.from_dict(project_data)

        return cls(
            global_log_repo=Path(global_log_repo).resolve()
            if global_log_repo
            else None,
            projects=projects,
        )

    def get_project_config(self, project_name: str) -> ProjectConfig:
        """Get configuration for a specific project."""
        return self.projects.get(project_name, ProjectConfig())

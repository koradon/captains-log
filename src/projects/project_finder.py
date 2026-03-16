"""Project discovery functionality for Captain's Log."""

from pathlib import Path
from typing import Optional

from src.config.config_models import Config, ProjectConfig
from src.projects.project_models import ProjectInfo


class ProjectFinder:
    """Handles finding and identifying projects from repository paths."""

    def __init__(self, config: Config):
        """Initialize with configuration."""
        self.config = config

    def find_project(self, repo_path: str) -> ProjectInfo:
        """Find project information from a repository path.

        Args:
            repo_path: Path to the repository directory

        Returns:
            ProjectInfo with project name and configuration
        """
        repo_path_abs = Path(repo_path).resolve()

        # Check configured projects first
        for project_name, project_config in self.config.projects.items():
            if project_config.root is None:
                continue

            root_abs = project_config.root.resolve()
            if root_abs in repo_path_abs.parents or root_abs == repo_path_abs:
                return ProjectInfo(
                    name=project_name, config=project_config, base_dir=root_abs
                )

        # Fallback: use repository name as project name
        project_name = repo_path_abs.name
        fallback_config = ProjectConfig(root=repo_path_abs)

        return ProjectInfo(
            name=project_name, config=fallback_config, base_dir=repo_path_abs
        )

    def get_project_by_name(self, project_name: str) -> Optional[ProjectInfo]:
        """Get project information by name.

        Args:
            project_name: Name of the project

        Returns:
            ProjectInfo if found, None otherwise
        """
        project_config = self.config.projects.get(project_name)
        if project_config is None:
            return None

        return ProjectInfo(
            name=project_name,
            config=project_config,
            base_dir=project_config.root or Path.cwd(),
        )

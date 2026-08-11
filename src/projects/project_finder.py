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

            # A repo checked out elsewhere (e.g. a treehouse/other pooled
            # worktree, which never lives under the configured root) still
            # belongs to this project if its directory name matches one of
            # root's own nested repos, so umbrella dirs like
            # ~/git/tripper/{facts-service,tripper-android-app} keep
            # grouping under "tripper" even when checked out elsewhere.
            if repo_path_abs.name in self._nested_repo_names(root_abs):
                return ProjectInfo(
                    name=project_name, config=project_config, base_dir=root_abs
                )

        # Fallback: use repository name as project name
        project_name = repo_path_abs.name
        fallback_config = ProjectConfig(root=repo_path_abs)

        return ProjectInfo(
            name=project_name, config=fallback_config, base_dir=repo_path_abs
        )

    def _nested_repo_names(self, root: Path) -> set:
        """Get the names of git repositories directly nested under root.

        Args:
            root: Directory to scan for nested git repositories

        Returns:
            Set of directory names (under root) that are themselves git repos
        """
        if not root.is_dir():
            return set()

        return {
            child.name
            for child in root.iterdir()
            if child.is_dir() and (child / ".git").exists()
        }

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

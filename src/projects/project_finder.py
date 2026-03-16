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

    @staticmethod
    def _find_git_root(path: Path) -> Optional[Path]:
        """Find the git repository root for a given path.

        Walks up the directory tree until a `.git` directory is found.
        Returns None if no git repository is found.
        """
        current = path
        while True:
            if (current / ".git").is_dir():
                return current

            parent = current.parent
            if parent == current:
                # Reached filesystem root
                return None

            current = parent

    def find_project(self, repo_path: str) -> ProjectInfo:
        """Find project information from a repository path.

        Args:
            repo_path: Path to the repository directory

        Returns:
            ProjectInfo with project name and configuration
        """
        repo_path_abs = Path(repo_path).resolve()

        # Prefer the git repository root when one exists.
        # This ensures that nested git repositories (e.g. a service inside
        # a larger mono-repo) are treated as their own logical projects
        # instead of inheriting the parent project configuration.
        git_root = self._find_git_root(repo_path_abs)
        target_path = git_root or repo_path_abs

        # First, look for an exact match between the target path and a
        # configured project root. This keeps existing behaviour for
        # explicitly-configured projects.
        for project_name, project_config in self.config.projects.items():
            if project_config.root is None:
                continue

            root_abs = project_config.root.resolve()
            if root_abs == target_path:
                return ProjectInfo(
                    name=project_name, config=project_config, base_dir=root_abs
                )

        # If we didn't find an exact match and we *don't* have a git root,
        # fall back to the original "ancestor match" behaviour so that
        # plain directories under a configured project still map to that
        # project.
        if git_root is None:
            for project_name, project_config in self.config.projects.items():
                if project_config.root is None:
                    continue

                root_abs = project_config.root.resolve()
                if root_abs in target_path.parents or root_abs == target_path:
                    return ProjectInfo(
                        name=project_name, config=project_config, base_dir=root_abs
                    )

        # Fallback: treat the git root (when present) or the given path
        # as an independent project identified by its directory name.
        project_name = target_path.name
        fallback_config = ProjectConfig(root=target_path)

        return ProjectInfo(
            name=project_name, config=fallback_config, base_dir=target_path
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

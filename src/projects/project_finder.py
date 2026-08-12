"""Project discovery functionality for Captain's Log."""

import configparser
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
            # Matching by name alone would silently misattribute an
            # unrelated repo that happens to share a common name (e.g.
            # "docs" or "api"), so we also require the two checkouts to
            # agree on their origin remote whenever both expose one.
            nested_repo = root_abs / repo_path_abs.name
            if (nested_repo / ".git").exists() and self._same_remote(
                repo_path_abs, nested_repo
            ):
                return ProjectInfo(
                    name=project_name, config=project_config, base_dir=root_abs
                )

        # Fallback: use repository name as project name
        project_name = repo_path_abs.name
        fallback_config = ProjectConfig(root=repo_path_abs)

        return ProjectInfo(
            name=project_name, config=fallback_config, base_dir=repo_path_abs
        )

    def _same_remote(self, repo_a: Path, repo_b: Path) -> bool:
        """Check whether two repos agree on their git origin remote.

        Repos with no resolvable remote (e.g. never pushed, or a local-only
        checkout) are treated as matching, since name-based matching is the
        best signal available for them. Repos that both expose a remote
        must agree, so two unrelated repos sharing a common directory name
        (e.g. "docs", "api") aren't silently merged into the same project.

        Args:
            repo_a: First repository directory
            repo_b: Second repository directory

        Returns:
            True if the repos are the same project by remote (or lack
            enough information to tell them apart), False if they have
            conflicting remotes
        """
        remote_a = self._git_remote_url(repo_a)
        remote_b = self._git_remote_url(repo_b)

        if remote_a is None or remote_b is None:
            return True

        return remote_a == remote_b

    def _git_remote_url(self, repo: Path) -> Optional[str]:
        """Read the "origin" remote URL from a repo's git config, if any.

        Args:
            repo: Path to the git repository (containing a `.git` dir)

        Returns:
            The origin remote URL, or None if unavailable
        """
        config_path = repo / ".git" / "config"
        if not config_path.is_file():
            return None

        parser = configparser.ConfigParser()
        try:
            parser.read(config_path)
        except configparser.Error:
            return None

        return parser.get('remote "origin"', "url", fallback=None)

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

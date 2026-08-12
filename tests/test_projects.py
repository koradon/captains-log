"""Tests for the projects module."""

import os
from pathlib import Path
from unittest.mock import patch

from src.config import Config, ProjectConfig
from src.projects import ProjectFinder, ProjectInfo


# ProjectInfo tests
def test_project_info_properties():
    """Test ProjectInfo properties."""
    config = ProjectConfig(root=Path("/tmp/test"), log_repo=Path("/tmp/logs"))
    info = ProjectInfo(name="test", config=config, base_dir=Path("/tmp/test"))

    assert info.name == "test"
    assert info.log_repo == Path("/tmp/logs")
    assert info.root_dir == Path("/tmp/test")
    assert info.base_dir == Path("/tmp/test")


def test_project_info_is_private_delegates_to_config():
    """Test that ProjectInfo.is_private delegates to ProjectConfig.is_private()."""
    private_config = ProjectConfig(root=Path("/tmp/test"), private=True)
    public_config = ProjectConfig(root=Path("/tmp/test"), private=False)

    with patch.dict(os.environ, {}, clear=True):
        private_info = ProjectInfo(
            name="secret", config=private_config, base_dir=Path("/tmp/test")
        )
        assert private_info.is_private is True

        public_info = ProjectInfo(
            name="public", config=public_config, base_dir=Path("/tmp/test")
        )
        assert public_info.is_private is False


# ProjectFinder tests
def test_project_finder_find_project_configured_match():
    """Test finding project from configured projects."""
    config = Config.from_dict(
        {
            "projects": {
                "work-project": {"root": "/path/to/work"},
                "personal": "/path/to/personal",
            }
        }
    )

    finder = ProjectFinder(config)
    project = finder.find_project("/path/to/work/subproject")

    assert project.name == "work-project"
    assert project.config.root == Path("/path/to/work").resolve()


def test_project_finder_find_project_exact_match():
    """Test finding project with exact path match."""
    config = Config.from_dict({"projects": {"exact-project": "/path/to/exact"}})

    finder = ProjectFinder(config)
    project = finder.find_project("/path/to/exact")

    assert project.name == "exact-project"
    assert project.config.root == Path("/path/to/exact").resolve()


def test_project_finder_find_project_fallback_to_repo_name():
    """Test fallback to repository name when no config match."""
    config = Config.from_dict({"projects": {}})

    finder = ProjectFinder(config)
    project = finder.find_project("/path/to/my-repo")

    assert project.name == "my-repo"
    assert project.config.root == Path("/path/to/my-repo").resolve()


def test_project_finder_find_project_nested_repo_checked_out_elsewhere(tmp_path):
    """Test that a repo nested under an umbrella project root is still
    grouped under that project even when checked out somewhere else
    entirely (e.g. a treehouse/pooled worktree that never lives under the
    configured root), as long as its directory name matches one of root's
    own nested git repos.
    """
    root = tmp_path / "tripper"
    (root / "facts-service" / ".git").mkdir(parents=True)

    elsewhere = tmp_path / "elsewhere" / "facts-service"
    (elsewhere / ".git").mkdir(parents=True)

    config = Config.from_dict({"projects": {"tripper": {"root": str(root)}}})
    finder = ProjectFinder(config)

    project = finder.find_project(str(elsewhere))

    assert project.name == "tripper"


def test_project_finder_find_project_same_name_different_remote_not_grouped(tmp_path):
    """Test that a same-named repo checked out elsewhere is NOT grouped
    under root's project when the two repos have conflicting origin
    remotes, since that indicates they are unrelated repos that happen to
    share a common directory name (e.g. "docs", "api").
    """
    root = tmp_path / "tripper"
    nested_git = root / "facts-service" / ".git"
    nested_git.mkdir(parents=True)
    (nested_git / "config").write_text(
        '[remote "origin"]\n\turl = git@github.com:tripper-org/facts-service.git\n'
    )

    elsewhere = tmp_path / "elsewhere" / "facts-service"
    elsewhere_git = elsewhere / ".git"
    elsewhere_git.mkdir(parents=True)
    (elsewhere_git / "config").write_text(
        '[remote "origin"]\n\turl = git@github.com:someone-else/facts-service.git\n'
    )

    config = Config.from_dict({"projects": {"tripper": {"root": str(root)}}})
    finder = ProjectFinder(config)

    project = finder.find_project(str(elsewhere))

    assert project.name == "facts-service"


def _make_worktree_checkout(worktree_dir, common_git_dir, remote_url):
    """Simulate a `git worktree add` checkout: `.git` is a *file* with a
    `gitdir:` pointer into `<common>/.git/worktrees/<name>`, which itself
    has a `commondir` file pointing back at the shared `.git` directory
    where `config` (and remotes) actually live.
    """
    worktree_name = worktree_dir.name
    worktree_git_dir = common_git_dir / "worktrees" / worktree_name
    worktree_git_dir.mkdir(parents=True)
    (worktree_git_dir / "commondir").write_text("../..\n")

    common_git_dir.mkdir(parents=True, exist_ok=True)
    (common_git_dir / "config").write_text(f'[remote "origin"]\n\turl = {remote_url}\n')

    worktree_dir.mkdir(parents=True, exist_ok=True)
    (worktree_dir / ".git").write_text(f"gitdir: {worktree_git_dir}\n")


def test_project_finder_find_project_pooled_worktree_same_remote_grouped(tmp_path):
    """Test that a pooled/treehouse `git worktree` checkout (where `.git`
    is a file, not a directory) is still correctly grouped under root's
    project when its resolved remote matches the nested repo's remote.
    """
    root = tmp_path / "tripper"
    nested_git = root / "facts-service" / ".git"
    nested_git.mkdir(parents=True)
    (nested_git / "config").write_text(
        '[remote "origin"]\n\turl = git@github.com:tripper-org/facts-service.git\n'
    )

    elsewhere = tmp_path / "pooled" / "facts-service"
    _make_worktree_checkout(
        elsewhere,
        tmp_path / "worktree-common" / ".git",
        "git@github.com:tripper-org/facts-service.git",
    )

    config = Config.from_dict({"projects": {"tripper": {"root": str(root)}}})
    finder = ProjectFinder(config)

    project = finder.find_project(str(elsewhere))

    assert project.name == "tripper"


def test_project_finder_find_project_pooled_worktree_different_remote_not_grouped(
    tmp_path,
):
    """Test that a pooled/treehouse `git worktree` checkout of an unrelated
    repo sharing the same directory name is NOT grouped under root's
    project, since its resolved remote disagrees.
    """
    root = tmp_path / "tripper"
    nested_git = root / "facts-service" / ".git"
    nested_git.mkdir(parents=True)
    (nested_git / "config").write_text(
        '[remote "origin"]\n\turl = git@github.com:tripper-org/facts-service.git\n'
    )

    elsewhere = tmp_path / "pooled" / "facts-service"
    _make_worktree_checkout(
        elsewhere,
        tmp_path / "worktree-common" / ".git",
        "git@github.com:someone-else/facts-service.git",
    )

    config = Config.from_dict({"projects": {"tripper": {"root": str(root)}}})
    finder = ProjectFinder(config)

    project = finder.find_project(str(elsewhere))

    assert project.name == "facts-service"


def test_project_finder_find_project_remote_url_with_percent_sign(tmp_path):
    """Test that a remote URL containing a literal '%' (e.g. a
    percent-encoded credential) doesn't raise a configparser interpolation
    error and is still compared correctly.
    """
    root = tmp_path / "tripper"
    nested_git = root / "facts-service" / ".git"
    nested_git.mkdir(parents=True)
    (nested_git / "config").write_text(
        '[remote "origin"]\n\turl = https://user:pa%40ss@github.com/tripper-org/facts-service.git\n'
    )

    elsewhere = tmp_path / "elsewhere" / "facts-service"
    elsewhere_git = elsewhere / ".git"
    elsewhere_git.mkdir(parents=True)
    (elsewhere_git / "config").write_text(
        '[remote "origin"]\n\turl = https://user:pa%40ss@github.com/tripper-org/facts-service.git\n'
    )

    config = Config.from_dict({"projects": {"tripper": {"root": str(root)}}})
    finder = ProjectFinder(config)

    project = finder.find_project(str(elsewhere))

    assert project.name == "tripper"


def test_project_finder_find_project_unrelated_name_not_grouped(tmp_path):
    """Test that a repo whose name doesn't match any nested repo under root
    still falls back to its own name, rather than being grouped by mistake.
    """
    root = tmp_path / "tripper"
    (root / "facts-service" / ".git").mkdir(parents=True)

    unrelated = tmp_path / "elsewhere" / "some-other-repo"
    (unrelated / ".git").mkdir(parents=True)

    config = Config.from_dict({"projects": {"tripper": {"root": str(root)}}})
    finder = ProjectFinder(config)

    project = finder.find_project(str(unrelated))

    assert project.name == "some-other-repo"


def test_project_finder_find_project_none_root():
    """Test handling of None root in project config."""
    config = Config.from_dict(
        {"projects": {"test-project": {"root": None, "log_repo": "/tmp/logs"}}}
    )

    finder = ProjectFinder(config)
    project = finder.find_project("/path/to/repo")

    # Should fallback to repo name since root is None
    assert project.name == "repo"


def test_project_finder_get_project_by_name_exists():
    """Test getting project by name when it exists."""
    config = Config.from_dict({"projects": {"test-project": "/tmp/test"}})

    finder = ProjectFinder(config)
    project = finder.get_project_by_name("test-project")

    assert project is not None
    assert project.name == "test-project"
    assert project.config.root == Path("/tmp/test").resolve()


def test_project_finder_get_project_by_name_not_exists():
    """Test getting project by name when it doesn't exist."""
    config = Config.from_dict({"projects": {}})

    finder = ProjectFinder(config)
    project = finder.get_project_by_name("nonexistent")

    assert project is None

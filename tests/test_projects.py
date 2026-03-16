"""Tests for the projects module."""

from pathlib import Path

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

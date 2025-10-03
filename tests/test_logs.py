"""Tests for the logs module."""

from datetime import date
from pathlib import Path
from unittest.mock import patch

from src.config import Config, ProjectConfig
from src.logs import LogData, LogFileInfo, LogManager, LogParser, LogWriter
from src.projects import ProjectInfo


# LogData tests
def test_log_data_empty_log_data():
    """Test empty log data."""
    log_data = LogData()
    assert log_data.repos == {}


def test_log_data_get_repo_entries():
    """Test getting repository entries."""
    log_data = LogData(repos={"test": ["entry1", "entry2"]})

    # Existing repo
    entries = log_data.get_repo_entries("test")
    assert entries == ["entry1", "entry2"]

    # Non-existing repo
    entries = log_data.get_repo_entries("nonexistent")
    assert entries == []


def test_log_data_set_repo_entries():
    """Test setting repository entries."""
    log_data = LogData()
    log_data.set_repo_entries("test", ["entry1", "entry2"])

    assert log_data.repos["test"] == ["entry1", "entry2"]


def test_log_data_add_repo_entry():
    """Test adding single repository entry."""
    log_data = LogData()
    log_data.add_repo_entry("test", "entry1")
    log_data.add_repo_entry("test", "entry2")

    assert log_data.repos["test"] == ["entry1", "entry2"]


def test_log_data_has_repo():
    """Test checking if repository exists."""
    log_data = LogData(repos={"test": []})

    assert log_data.has_repo("test") is True
    assert log_data.has_repo("nonexistent") is False


# LogFileInfo tests
def test_log_file_info_properties(tmp_path):
    """Test LogFileInfo properties."""
    file_path = tmp_path / "test.md"
    log_repo_path = tmp_path / "repo"
    test_date = date(2024, 1, 15)

    info = LogFileInfo(
        file_path=file_path,
        log_repo_path=log_repo_path,
        project_name="test-project",
        date_created=test_date,
    )

    assert info.file_name == "test.md"
    assert info.project_name == "test-project"
    assert info.date_created == test_date
    assert info.has_git_repo is True
    assert info.exists is False  # File doesn't exist yet


def test_log_file_info_exists_true(tmp_path):
    """Test exists property when file exists."""
    file_path = tmp_path / "test.md"
    file_path.write_text("test")

    info = LogFileInfo(
        file_path=file_path,
        log_repo_path=None,
        project_name="test",
        date_created=date.today(),
    )

    assert info.exists is True
    assert info.has_git_repo is False


# LogParser tests
def test_log_parser_parse_log_file_not_exists(tmp_path):
    """Test parsing non-existent log file."""
    file_path = tmp_path / "nonexistent.md"
    log_data = LogParser.parse_log_file(file_path)

    assert log_data.repos == {}


def test_log_parser_parse_log_file_with_content(tmp_path):
    """Test parsing log file with content."""
    content = """# What I did

## repo1
- (abc123) First commit
- (def456) Second commit

## repo2
- (ghi789) Another commit

# Whats next

# What Broke or Got Weird
"""
    file_path = tmp_path / "test.md"
    file_path.write_text(content)

    log_data = LogParser.parse_log_file(file_path)
    expected = {
        "repo1": ["- (abc123) First commit", "- (def456) Second commit"],
        "repo2": ["- (ghi789) Another commit"],
    }
    assert log_data.repos == expected


def test_log_parser_parse_log_file_unicode_error(tmp_path):
    """Test handling unicode decode error."""
    file_path = tmp_path / "test.md"
    file_path.write_bytes(b"\xff\xfe\x00\x00")  # Invalid UTF-8

    with patch("builtins.print") as mock_print:
        log_data = LogParser.parse_log_file(file_path)
        assert log_data.repos == {}
        mock_print.assert_called()


def test_log_parser_parse_log_content():
    """Test parsing log content from string."""
    content = """# What I did

## test-repo
- (abc123) Test commit

# Footer"""

    log_data = LogParser.parse_log_content(content)
    assert log_data.repos == {"test-repo": ["- (abc123) Test commit"]}


# LogWriter tests
def test_log_writer_write_log_file_new(tmp_path):
    """Test writing to new log file."""
    file_path = tmp_path / "logs" / "test.md"
    log_data = LogData(repos={"repo1": ["- (abc123) Test commit"]})

    writer = LogWriter()
    writer.write_log_file(file_path, log_data)

    assert file_path.exists()
    content = file_path.read_text()
    assert "# What I did" in content
    assert "## repo1" in content
    assert "- (abc123) Test commit" in content
    assert "# Whats next" in content
    assert "# What Broke or Got Weird" in content


def test_log_writer_write_log_file_other_at_end(tmp_path):
    """Test writing with 'other' section at end."""
    file_path = tmp_path / "test.md"
    log_data = LogData(
        repos={
            "zebra": ["- Zebra entry"],
            "other": ["- Manual entry"],
            "alpha": ["- Alpha entry"],
        }
    )

    writer = LogWriter()
    writer.write_log_file(file_path, log_data)

    content = file_path.read_text()

    # Check order: alpha, zebra, other
    alpha_pos = content.find("## alpha")
    zebra_pos = content.find("## zebra")
    other_pos = content.find("## other")

    assert alpha_pos < zebra_pos < other_pos


def test_log_writer_write_log_file_existing_corrupted(tmp_path):
    """Test writing when existing file is corrupted."""
    file_path = tmp_path / "test.md"
    file_path.write_text("Corrupted content")

    log_data = LogData(repos={"repo1": ["- (abc123) Test commit"]})

    writer = LogWriter()
    writer.write_log_file(file_path, log_data)

    content = file_path.read_text()
    assert "# What I did" in content
    assert "# Whats next" in content


def test_log_writer_get_log_template():
    """Test getting log template."""
    writer = LogWriter()
    template = writer.get_log_template()

    assert "# What I did" in template
    assert "# Whats next" in template
    assert "# What Broke or Got Weird" in template


# LogManager tests
def test_log_manager_get_log_file_info_global_repo():
    """Test getting log file info with global repository."""
    config = Config.from_dict({"global_log_repo": "/tmp/global-logs"})
    project_config = ProjectConfig(root=Path("/tmp/project"))
    project = ProjectInfo(
        name="test-project", config=project_config, base_dir=Path("/tmp/project")
    )

    manager = LogManager(config)

    with patch("src.logs.log_manager.date") as mock_date:
        mock_date.today.return_value = date(2024, 1, 15)
        log_info = manager.get_log_file_info(project)

    assert log_info.log_repo_path == Path("/tmp/global-logs").resolve()
    assert log_info.file_path.name == "2024.01.15.md"
    assert log_info.file_path.parent == log_info.log_repo_path / "test-project"
    assert log_info.has_git_repo is True


def test_log_manager_get_log_file_info_project_specific():
    """Test getting log file info with project-specific repository."""
    config = Config.from_dict({})
    project_config = ProjectConfig(
        root=Path("/tmp/project"), log_repo=Path("/tmp/project-logs")
    )
    project = ProjectInfo(
        name="test-project", config=project_config, base_dir=Path("/tmp/project")
    )

    manager = LogManager(config)

    with patch("src.logs.log_manager.date") as mock_date:
        mock_date.today.return_value = date(2024, 1, 15)
        log_info = manager.get_log_file_info(project)

    assert log_info.log_repo_path == Path("/tmp/project-logs").resolve()
    assert log_info.file_path.name == "2024.01.15.md"
    assert log_info.file_path.parent == log_info.log_repo_path
    assert log_info.has_git_repo is True


def test_log_manager_get_log_file_info_no_repo():
    """Test getting log file info with no repository."""
    config = Config.from_dict({})
    project_config = ProjectConfig(root=Path("/tmp/project"))
    project = ProjectInfo(
        name="test-project", config=project_config, base_dir=Path("/tmp/project")
    )

    manager = LogManager(config)

    with patch("src.logs.log_manager.date") as mock_date:
        mock_date.today.return_value = date(2024, 1, 15)
        log_info = manager.get_log_file_info(project)

    assert log_info.log_repo_path is None
    assert log_info.file_path.name == "2024.01.15.md"
    assert log_info.file_path.parent == LogManager.BASE_DIR / "test-project"
    assert log_info.has_git_repo is False


def test_log_manager_load_log(tmp_path):
    """Test loading log through manager."""
    config = Config.from_dict({})
    manager = LogManager(config)

    # Create test log file
    log_file = tmp_path / "test.md"
    log_file.write_text(
        """# What I did

## test-repo
- (abc123) Test commit
"""
    )

    log_info = LogFileInfo(
        file_path=log_file,
        log_repo_path=None,
        project_name="test",
        date_created=date.today(),
    )

    log_data = manager.load_log(log_info)
    assert log_data.repos == {"test-repo": ["- (abc123) Test commit"]}


def test_log_manager_save_log(tmp_path):
    """Test saving log through manager."""
    config = Config.from_dict({})
    manager = LogManager(config)

    log_file = tmp_path / "test.md"
    log_info = LogFileInfo(
        file_path=log_file,
        log_repo_path=None,
        project_name="test",
        date_created=date.today(),
    )

    log_data = LogData(repos={"test-repo": ["- (abc123) Test commit"]})
    manager.save_log(log_info, log_data)

    assert log_file.exists()
    content = log_file.read_text()
    assert "## test-repo" in content
    assert "- (abc123) Test commit" in content

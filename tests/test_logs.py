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


def test_log_manager_get_log_file_info_past_month(tmp_path):
    """Test getting log file info for past month uses year/month subdirectory."""
    config = Config.from_dict({})
    project_config = ProjectConfig(root=Path("/tmp/project"))
    project = ProjectInfo(
        name="test-project", config=project_config, base_dir=Path("/tmp/project")
    )

    manager = LogManager(config)

    # Mock today as 2024-03-15, request log for 2024-02-10 (past month)
    with patch("src.logs.log_manager.date") as mock_date:
        mock_date.today.return_value = date(2024, 3, 15)
        log_info = manager.get_log_file_info(project, log_date=date(2024, 2, 10))

    assert log_info.file_path.name == "2024.02.10.md"
    # Should be in year/month subdirectory
    assert log_info.file_path.parent.name == "02"
    assert log_info.file_path.parent.parent.name == "2024"
    assert (
        log_info.file_path.parent.parent.parent == LogManager.BASE_DIR / "test-project"
    )


def test_log_manager_get_log_file_info_current_month(tmp_path):
    """Test getting log file info for current month stays in base directory."""
    config = Config.from_dict({})
    project_config = ProjectConfig(root=Path("/tmp/project"))
    project = ProjectInfo(
        name="test-project", config=project_config, base_dir=Path("/tmp/project")
    )

    manager = LogManager(config)

    # Mock today as 2024-03-15, request log for same date (current month)
    with patch("src.logs.log_manager.date") as mock_date:
        mock_date.today.return_value = date(2024, 3, 15)
        log_info = manager.get_log_file_info(project, log_date=date(2024, 3, 15))

    assert log_info.file_path.name == "2024.03.15.md"
    # Should be in base directory, not in year/month subdirectory
    assert log_info.file_path.parent == LogManager.BASE_DIR / "test-project"


def test_log_manager_organize_old_files(tmp_path):
    """Test that old log files are moved to year/month directories."""
    config = Config.from_dict({})
    project_config = ProjectConfig(root=Path("/tmp/project"))
    project = ProjectInfo(
        name="test-project", config=project_config, base_dir=tmp_path / "test-project"
    )

    # Patch BASE_DIR first, then create base directory in the correct location
    base_dir = tmp_path / ".captains-log" / "projects" / "test-project"
    base_dir.mkdir(parents=True)

    # Create old log files in base directory (from previous month)
    old_file1 = base_dir / "2024.01.15.md"
    old_file1.write_text("# Old log 1")
    old_file2 = base_dir / "2024.01.20.md"
    old_file2.write_text("# Old log 2")

    # Create current month log file
    current_file = base_dir / "2024.03.10.md"
    current_file.write_text("# Current log")

    manager = LogManager(config)

    # Mock today as 2024-03-15 and patch BASE_DIR to use tmp_path
    with patch("src.logs.log_manager.date") as mock_date, patch.object(
        LogManager, "BASE_DIR", tmp_path / ".captains-log" / "projects"
    ):
        mock_date.today.return_value = date(2024, 3, 15)
        # Trigger organization by getting log file info for current month
        manager.get_log_file_info(project)

    # Old files should be moved to year/month subdirectory
    assert not old_file1.exists()
    assert not old_file2.exists()
    assert (base_dir / "2024" / "01" / "2024.01.15.md").exists()
    assert (base_dir / "2024" / "01" / "2024.01.20.md").exists()

    # Current month file should remain in base directory
    assert current_file.exists()


def test_log_manager_load_log_fallback(tmp_path):
    """Test loading log with fallback to old location."""
    config = Config.from_dict({})
    manager = LogManager(config)

    # Mock BASE_DIR to point to tmp_path
    base_dir = tmp_path / ".captains-log" / "projects" / "test-project"
    base_dir.mkdir(parents=True)

    # Create a log file in the old location (base directory)
    old_log_file = base_dir / "2024.01.15.md"
    old_log_file.write_text(
        """# What I did

## test-repo
- (abc123) Test commit
"""
    )

    # Create log_info pointing to new location (year/month subdirectory)
    # but file hasn't been moved yet
    log_info = LogFileInfo(
        file_path=base_dir / "2024" / "01" / "2024.01.15.md",
        log_repo_path=None,
        project_name="test-project",
        date_created=date(2024, 1, 15),
    )

    with patch.object(LogManager, "BASE_DIR", tmp_path / ".captains-log" / "projects"):
        # Should find file in old location via fallback
        log_data = manager.load_log(log_info)
        assert log_data.repos == {"test-repo": ["- (abc123) Test commit"]}


def test_log_manager_organize_multiple_months(tmp_path):
    """Test organizing log files from multiple past months."""
    config = Config.from_dict({})
    project_config = ProjectConfig(root=Path("/tmp/project"))
    project = ProjectInfo(
        name="test-project", config=project_config, base_dir=tmp_path / "test-project"
    )

    # Patch BASE_DIR first, then create base directory in the correct location
    base_dir = tmp_path / ".captains-log" / "projects" / "test-project"
    base_dir.mkdir(parents=True)

    # Create log files from multiple past months (simulating months of usage)
    # November 2024
    nov_file1 = base_dir / "2024.11.05.md"
    nov_file1.write_text("# Nov log 1")
    nov_file2 = base_dir / "2024.11.15.md"
    nov_file2.write_text("# Nov log 2")

    # December 2024
    dec_file1 = base_dir / "2024.12.01.md"
    dec_file1.write_text("# Dec log 1")
    dec_file2 = base_dir / "2024.12.20.md"
    dec_file2.write_text("# Dec log 2")

    # January 2025
    jan_file1 = base_dir / "2025.01.10.md"
    jan_file1.write_text("# Jan log 1")
    jan_file2 = base_dir / "2025.01.25.md"
    jan_file2.write_text("# Jan log 2")

    # Current month (March 2025)
    current_file = base_dir / "2025.03.10.md"
    current_file.write_text("# Current log")

    manager = LogManager(config)

    # Mock today as 2025-03-15 and patch BASE_DIR to use tmp_path
    with patch("src.logs.log_manager.date") as mock_date, patch.object(
        LogManager, "BASE_DIR", tmp_path / ".captains-log" / "projects"
    ):
        mock_date.today.return_value = date(2025, 3, 15)
        # Trigger organization by getting log file info for current month
        manager.get_log_file_info(project)

    # All old files should be moved to their respective year/month subdirectories
    assert not nov_file1.exists()
    assert not nov_file2.exists()
    assert not dec_file1.exists()
    assert not dec_file2.exists()
    assert not jan_file1.exists()
    assert not jan_file2.exists()

    # November files should be in 2024/11/
    assert (base_dir / "2024" / "11" / "2024.11.05.md").exists()
    assert (base_dir / "2024" / "11" / "2024.11.15.md").exists()

    # December files should be in 2024/12/
    assert (base_dir / "2024" / "12" / "2024.12.01.md").exists()
    assert (base_dir / "2024" / "12" / "2024.12.20.md").exists()

    # January files should be in 2025/01/
    assert (base_dir / "2025" / "01" / "2025.01.10.md").exists()
    assert (base_dir / "2025" / "01" / "2025.01.25.md").exists()

    # Current month file should remain in base directory
    assert current_file.exists()

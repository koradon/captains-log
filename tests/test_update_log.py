import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

import update_log


# Test find_project function
def test_find_project_configured_match():
    """Test finding project from configured projects"""
    config = {
        "projects": {"work-project": "/path/to/work", "personal": "/path/to/personal"}
    }

    result = update_log.find_project("/path/to/work/subproject", config)
    assert result == "work-project"


def test_find_project_exact_match():
    """Test finding project with exact path match"""
    config = {"projects": {"exact-project": "/path/to/exact"}}

    result = update_log.find_project("/path/to/exact", config)
    assert result == "exact-project"


def test_find_project_fallback_to_repo_name():
    """Test fallback to repository name when no config match"""
    config = {"projects": {}}

    result = update_log.find_project("/path/to/my-repo", config)
    assert result == "my-repo"


def test_find_project_none_root():
    """Test handling of None root in project config"""
    config = {"projects": {"test-project": {"root": None, "log_repo": "/tmp/logs"}}}

    result = update_log.find_project("/path/to/repo", config)
    assert result == "repo"


# Test load_log function
def test_load_log_file_not_exists(tmp_path):
    """Test loading log from non-existent file"""
    log_file = tmp_path / "nonexistent.md"
    result = update_log.load_log(log_file)
    assert result == {}


def test_load_log_empty_file(tmp_path):
    """Test loading log from empty file"""
    log_file = tmp_path / "empty.md"
    log_file.write_text("")
    result = update_log.load_log(log_file)
    assert result == {}


def test_load_log_with_content(tmp_path):
    """Test loading log with valid content"""
    content = """# What I did

## repo1
- (abc123) First commit
- (def456) Second commit

## repo2
- (ghi789) Another commit

# Whats next

# What Broke or Got Weird
"""
    log_file = tmp_path / "test.md"
    log_file.write_text(content)

    result = update_log.load_log(log_file)
    expected = {
        "repo1": ["- (abc123) First commit", "- (def456) Second commit"],
        "repo2": ["- (ghi789) Another commit"],
    }
    assert result == expected


def test_load_log_unicode_error(tmp_path):
    """Test handling of unicode decode errors"""
    log_file = tmp_path / "test.md"
    log_file.write_bytes(b"\xff\xfe\x00\x00")  # Invalid UTF-8

    with patch("builtins.print") as mock_print:
        result = update_log.load_log(log_file)
        assert result == {}
        mock_print.assert_called()


# Test parse_commit_entry function
def test_parse_commit_entry_valid():
    """Test parsing valid commit entry"""
    entry = "- (abc1234) This is a commit message"
    sha, message = update_log.parse_commit_entry(entry)
    assert sha == "abc1234"
    assert message == "This is a commit message"


def test_parse_commit_entry_invalid_format():
    """Test parsing invalid commit entry format"""
    entry = "This is not a commit entry"
    sha, message = update_log.parse_commit_entry(entry)
    assert sha is None
    assert message is None


def test_parse_commit_entry_missing_message():
    """Test parsing commit entry with missing message"""
    entry = "- (abc1234) "
    sha, message = update_log.parse_commit_entry(entry)
    assert sha == "abc1234"
    assert message == ""


# Test update_commit_entries function
def test_update_commit_entries_new_entry():
    """Test adding new commit entry"""
    entries = ["- (abc123) Old commit"]
    new_sha = "def456789"
    new_msg = "New commit"

    result = update_log.update_commit_entries(entries, new_sha, new_msg)
    expected = ["- (abc123) Old commit", "- (def4567) New commit"]
    assert result == expected


def test_update_commit_entries_duplicate_message():
    """Test removing duplicate message entries"""
    entries = [
        "- (abc123) Same message",
        "- (def456) Another commit",
        "- (ghi789) Same message",
    ]
    new_sha = "jkl012"
    new_msg = "Same message"

    result = update_log.update_commit_entries(entries, new_sha, new_msg)
    expected = ["- (def456) Another commit", "- (jkl012) Same message"]
    assert result == expected


def test_update_commit_entries_exact_match():
    """Test when exact SHA and message already exist"""
    entries = ["- (abc123) Existing message"]
    new_sha = "abc123"
    new_msg = "Existing message"

    result = update_log.update_commit_entries(entries, new_sha, new_msg)
    assert result == entries  # Should not change


def test_update_commit_entries_short_sha():
    """Test handling of short SHA"""
    entries = []
    new_sha = "abc"
    new_msg = "Short SHA commit"

    result = update_log.update_commit_entries(entries, new_sha, new_msg)
    expected = ["- (abc) Short SHA commit"]
    assert result == expected


# Test save_log function
def test_save_log_new_file(tmp_path):
    """Test saving log to new file"""
    log_file = tmp_path / "logs" / "test.md"
    repos = {"repo1": ["- (abc123) Test commit"]}

    update_log.save_log(log_file, repos)

    assert log_file.exists()
    content = log_file.read_text()
    assert "# What I did" in content
    assert "## repo1" in content
    assert "- (abc123) Test commit" in content
    assert "# Whats next" in content
    assert "# What Broke or Got Weird" in content


def test_save_log_existing_file(tmp_path):
    """Test saving log to existing file"""
    log_file = tmp_path / "test.md"
    existing_content = """# What I did

## old-repo
- (old123) Old commit

# Whats next

# What Broke or Got Weird
"""
    log_file.write_text(existing_content)

    repos = {"new-repo": ["- (new456) New commit"]}
    update_log.save_log(log_file, repos)

    content = log_file.read_text()
    assert "## new-repo" in content
    assert "- (new456) New commit" in content
    assert "## old-repo" not in content  # Should be replaced


def test_save_log_corrupted_file(tmp_path):
    """Test saving log when existing file is corrupted"""
    log_file = tmp_path / "test.md"
    log_file.write_text("Corrupted content without headers")

    repos = {"repo1": ["- (abc123) Test commit"]}
    update_log.save_log(log_file, repos)

    content = log_file.read_text()
    assert "# What I did" in content
    assert "# Whats next" in content


# Test get_log_repo_and_path function
def test_get_log_repo_and_path_global_repo():
    """Test getting path with global log repo"""
    config = {"global_log_repo": "/tmp/global-logs"}
    project = "test-project"

    # Skip date mocking for legacy test - just test basic functionality
    log_repo_path, log_file = update_log.get_log_repo_and_path(project, config)

    assert log_repo_path == Path("/tmp/global-logs").resolve()
    assert log_file.name.endswith(".md")
    assert log_file.parent == log_repo_path / project


def test_get_log_repo_and_path_project_specific():
    """Test getting path with project-specific log repo"""
    config = {
        "projects": {
            "test-project": {"log_repo": "/tmp/project-logs", "root": "/tmp/project"}
        }
    }
    project = "test-project"

    # Skip date mocking for legacy test - just test basic functionality
    log_repo_path, log_file = update_log.get_log_repo_and_path(project, config)

    assert log_repo_path == Path("/tmp/project-logs").resolve()
    assert log_file.name.endswith(".md")
    assert log_file.parent == log_repo_path


def test_get_log_repo_and_path_no_repo():
    """Test getting path when no log repo is configured"""
    config = {}
    project = "test-project"

    # Skip date mocking for legacy test - just test basic functionality
    log_repo_path, log_file = update_log.get_log_repo_and_path(project, config)

    assert log_repo_path is None
    assert log_file.name.endswith(".md")
    assert log_file.parent == update_log.BASE_DIR / project


# Test commit_and_push function
@patch("subprocess.run")
def test_commit_and_push_success(mock_run, tmp_path):
    """Test successful commit and push"""
    log_repo_path = tmp_path / "log-repo"
    log_repo_path.mkdir()
    (log_repo_path / ".git").mkdir()

    file_path = log_repo_path / "test.md"  # Make sure file is inside repo
    file_path.write_text("test content")

    # Mock git status to show changes
    mock_run.side_effect = [
        MagicMock(stdout="M  test.md"),  # status
        MagicMock(),  # add
        MagicMock(),  # commit
        MagicMock(),  # push
    ]

    update_log.commit_and_push(log_repo_path, "Test commit")

    assert mock_run.call_count == 4


@patch("subprocess.run")
def test_commit_and_push_no_changes(mock_run, tmp_path):
    """Test commit and push when no changes exist"""
    log_repo_path = tmp_path / "log-repo"
    log_repo_path.mkdir()
    (log_repo_path / ".git").mkdir()

    file_path = tmp_path / "test.md"
    file_path.write_text("test content")

    # Mock git status to show no changes
    mock_run.return_value = MagicMock(stdout="")

    with patch("builtins.print") as mock_print:
        update_log.commit_and_push(log_repo_path, "Test commit")
        mock_print.assert_called_with("No changes to commit, skipping git operations")


@patch("subprocess.run")
def test_commit_and_push_git_error(mock_run, tmp_path):
    """Test handling of git errors"""
    log_repo_path = tmp_path / "log-repo"
    log_repo_path.mkdir()
    (log_repo_path / ".git").mkdir()

    file_path = tmp_path / "test.md"
    file_path.write_text("test content")

    # Mock git status to fail
    mock_run.side_effect = subprocess.CalledProcessError(1, "git status")

    with patch("builtins.print") as mock_print:
        update_log.commit_and_push(log_repo_path, "Test commit")
        mock_print.assert_called()


def test_main_insufficient_args(monkeypatch):
    """Test main with insufficient arguments"""
    # Set up insufficient arguments
    monkeypatch.setattr(sys, "argv", ["update_log.py", "repo1", "/tmp/repo1"])

    update_log.main()


@patch("builtins.print")
@patch("sys.argv", ["update_log.py", "repo1", "/tmp/repo1", "no-sha", "Test commit"])
def test_main_no_sha(mock_print):
    """Test main with no-sha commit"""
    update_log.main()
    mock_print.assert_called_with("Skipping log update: No valid commit SHA")


@patch("builtins.print")
@patch(
    "sys.argv", ["update_log.py", "repo1", "/tmp/repo1", "no-sha-merge", "Merge branch"]
)
def test_main_merge_commit(mock_print):
    """Test main with merge commit"""
    update_log.main()
    mock_print.assert_called_with("Skipping log update: No valid commit SHA")


# Integration tests
@pytest.mark.integration
def test_full_workflow(tmp_path):
    """Test the complete workflow from config to saved log"""
    # Create config
    config_data = {
        "global_log_repo": str(tmp_path / "global-logs"),
        "projects": {"test-project": str(tmp_path / "test-project")},
    }
    config_file = tmp_path / "config.yml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Create project directory
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    with patch("update_log.CONFIG_FILE", config_file):
        # Test the full workflow
        config = update_log.load_config()
        project = update_log.find_project(str(project_dir), config)
        log_repo_path, log_file = update_log.get_log_repo_and_path(project, config)

        # Create initial log
        repos = {"test-repo": []}
        update_log.save_log(log_file, repos)

        # Update with commit
        repos["test-repo"] = update_log.update_commit_entries(
            repos["test-repo"], "abc123456", "Test commit message"
        )
        update_log.save_log(log_file, repos)

        # Verify result
        assert log_file.exists()
        content = log_file.read_text()
        assert "## test-repo" in content
        assert "- (abc1234) Test commit message" in content


@patch("subprocess.run")
def test_update_log_commit_uses_add_all(mock_run, tmp_path):
    """Test that commit_and_push uses add_all() to stage all changes."""
    import yaml

    # Create a git repository
    log_repo_path = tmp_path / "log-repo"
    log_repo_path.mkdir()
    (log_repo_path / ".git").mkdir()

    # Create config file
    config_data = {
        "global_log_repo": str(log_repo_path),
        "projects": {"test-project": str(tmp_path / "test-project")},
    }
    config_file = tmp_path / "config.yml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Create project directory
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Create project directory structure
    base_dir = tmp_path / ".captains-log" / "projects" / "test-project"
    base_dir.mkdir(parents=True)

    # Create current month log file
    from datetime import date

    today = date.today()
    current_file = base_dir / f"{today.year}.{today.month:02d}.{today.day:02d}.md"
    current_file.write_text("# Current log\n## test-repo\n")

    # Mock git operations: status (shows changes), add_all, commit, push
    mock_run.side_effect = [
        MagicMock(stdout=f"M  {current_file.name}"),  # status - has changes
        MagicMock(),  # add_all
        MagicMock(),  # commit
        MagicMock(),  # push
    ]

    # Patch sys.argv and config loading
    from src.config.config_loader import set_config_path

    with patch.object(
        update_log.LogManager, "BASE_DIR", tmp_path / ".captains-log" / "projects"
    ), patch(
        "sys.argv",
        [
            "update_log.py",
            "test-repo",
            str(project_dir),
            "abc123456",
            "Test commit message",
        ],
    ):
        # Set config path before running main
        set_config_path(config_file)
        # Run update_log.main which should commit with add_all
        update_log.main()

    # Verify git operations were called in correct order: status, add_all, commit, push
    assert mock_run.call_count == 4

    # Get all call arguments
    all_calls = [call[0][0] for call in mock_run.call_args_list]

    # Verify add_all was called (not add_file) - should contain "add", "-A"
    add_all_found = any(
        call == ["git", "-C", str(log_repo_path), "add", "-A"] for call in all_calls
    )
    assert add_all_found, f"add_all should have been called. Calls: {all_calls}"

    # Verify commit was called (commit has format: ['git', '-C', path, 'commit', '-m', 'message'])
    commit_found = any(
        len(call) >= 4 and call[0] == "git" and call[1] == "-C" and call[3] == "commit"
        for call in all_calls
    )
    assert commit_found, f"commit should have been called. Calls: {all_calls}"

    # Verify push was called
    push_found = any(
        call == ["git", "-C", str(log_repo_path), "push"] for call in all_calls
    )
    assert push_found, f"push should have been called. Calls: {all_calls}"

"""Tests for the git module."""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.git import GitOperations, CommitParser


# CommitParser tests
def test_commit_parser_is_valid_commit_sha_valid():
    """Test valid commit SHAs."""
    valid_shas = ["abc123", "def456789", "1234567890abcdef"]
    
    for sha in valid_shas:
        assert CommitParser.is_valid_commit_sha(sha) is True


def test_commit_parser_is_valid_commit_sha_invalid():
    """Test invalid commit SHAs."""
    invalid_shas = ["", "no-sha", "no-sha-merge", None]
    
    for sha in invalid_shas:
        assert CommitParser.is_valid_commit_sha(sha) is False


def test_commit_parser_parse_commit_entry_valid():
    """Test parsing valid commit entry."""
    entry = "- (abc1234) This is a commit message"
    sha, message = CommitParser.parse_commit_entry(entry)
    assert sha == "abc1234"
    assert message == "This is a commit message"


def test_commit_parser_parse_commit_entry_invalid():
    """Test parsing invalid commit entry."""
    invalid_entries = [
        "This is not a commit entry",
        "- Not a commit",
        "- (abc1234",  # Missing closing paren
    ]
    
    for entry in invalid_entries:
        sha, message = CommitParser.parse_commit_entry(entry)
        assert sha is None
        assert message is None


def test_commit_parser_should_skip_commit_invalid_sha():
    """Test skipping commits with invalid SHAs."""
    assert CommitParser.should_skip_commit("no-sha", "/tmp/repo", None) is True
    assert CommitParser.should_skip_commit("", "/tmp/repo", None) is True


def test_commit_parser_should_skip_commit_log_repo():
    """Test skipping commits from log repository itself."""
    # Same repository
    assert CommitParser.should_skip_commit("abc123", "/tmp/logs", "/tmp/logs") is True
    
    # Different repository
    assert CommitParser.should_skip_commit("abc123", "/tmp/repo", "/tmp/logs") is False


def test_commit_parser_should_skip_commit_valid():
    """Test not skipping valid commits."""
    assert CommitParser.should_skip_commit("abc123", "/tmp/repo", None) is False


# GitOperations tests
def test_git_operations_init(tmp_path):
    """Test GitOperations initialization."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)
    assert git_ops.repo_path == repo_path


@patch('subprocess.run')
def test_git_operations_has_changes_true(mock_run, tmp_path):
    """Test has_changes when changes exist."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)
    
    mock_run.return_value = MagicMock(stdout="M  file.txt")
    assert git_ops.has_changes() is True


@patch('subprocess.run')
def test_git_operations_has_changes_false(mock_run, tmp_path):
    """Test has_changes when no changes exist."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)
    
    mock_run.return_value = MagicMock(stdout="")
    assert git_ops.has_changes() is False


@patch('subprocess.run')
def test_git_operations_has_changes_error(mock_run, tmp_path):
    """Test has_changes when git command fails."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)
    
    mock_run.side_effect = subprocess.CalledProcessError(1, "git")
    assert git_ops.has_changes() is False


def test_git_operations_has_lock_files_true(tmp_path):
    """Test has_lock_files when lock files exist."""
    repo_path = tmp_path / "repo"
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "index.lock").write_text("")
    
    git_ops = GitOperations(repo_path)
    assert git_ops.has_lock_files() is True


def test_git_operations_has_lock_files_false(tmp_path):
    """Test has_lock_files when no lock files exist."""
    repo_path = tmp_path / "repo"
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True)
    
    git_ops = GitOperations(repo_path)
    assert git_ops.has_lock_files() is False


def test_git_operations_has_lock_files_no_git_dir(tmp_path):
    """Test has_lock_files when .git directory doesn't exist."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    
    git_ops = GitOperations(repo_path)
    assert git_ops.has_lock_files() is False
    
@patch('subprocess.run')
def test_git_operations_add_file_success(mock_run, tmp_path):
    """Test successful file addition."""
    repo_path = tmp_path / "repo"
    file_path = repo_path / "test.txt"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("test")
    
    git_ops = GitOperations(repo_path)
    assert git_ops.add_file(file_path) is True
    mock_run.assert_called_once()


@patch('subprocess.run')
def test_git_operations_add_file_error(mock_run, tmp_path):
    """Test file addition error."""
    repo_path = tmp_path / "repo"
    file_path = repo_path / "test.txt"
    
    mock_run.side_effect = subprocess.CalledProcessError(1, "git")
    git_ops = GitOperations(repo_path)
    assert git_ops.add_file(file_path) is False


@patch('subprocess.run')
def test_git_operations_commit_success(mock_run, tmp_path):
    """Test successful commit."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)
    
    assert git_ops.commit("Test commit") is True
    mock_run.assert_called_once()


@patch('subprocess.run')
def test_git_operations_commit_error(mock_run, tmp_path):
    """Test commit error."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)
    
    mock_run.side_effect = subprocess.CalledProcessError(1, "git")
    assert git_ops.commit("Test commit") is False


@patch('subprocess.run')
def test_git_operations_push_success(mock_run, tmp_path):
    """Test successful push."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)
    
    assert git_ops.push() is True
    mock_run.assert_called_once()


@patch('subprocess.run')
def test_git_operations_push_error(mock_run, tmp_path):
    """Test push error."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)
    
    mock_run.side_effect = subprocess.CalledProcessError(1, "git")
    assert git_ops.push() is False
    
@patch('subprocess.run')
def test_git_operations_commit_and_push_success(mock_run, tmp_path):
    """Test successful commit and push workflow."""
    repo_path = tmp_path / "repo"
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True)
    
    file_path = repo_path / "test.txt"
    file_path.write_text("test")
    
    # Mock git operations: status, add, commit, push
    mock_run.side_effect = [
        MagicMock(stdout="M  test.txt"),  # status - has changes
        MagicMock(),  # add
        MagicMock(),  # commit
        MagicMock()   # push
    ]
    
    git_ops = GitOperations(repo_path)
    result = git_ops.commit_and_push(file_path, "Test commit")
    
    assert result is True
    assert mock_run.call_count == 4


def test_git_operations_commit_and_push_lock_files(tmp_path):
    """Test commit and push with lock files present."""
    repo_path = tmp_path / "repo"
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "index.lock").write_text("")
    
    file_path = repo_path / "test.txt"
    
    git_ops = GitOperations(repo_path)
    with patch('builtins.print') as mock_print:
        result = git_ops.commit_and_push(file_path, "Test commit")
        assert result is False
        mock_print.assert_called_with("Warning: Git lock files found, skipping operations")


@patch('subprocess.run')
def test_git_operations_commit_and_push_no_changes(mock_run, tmp_path):
    """Test commit and push when no changes exist."""
    repo_path = tmp_path / "repo"
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True)
    
    file_path = repo_path / "test.txt"
    
    # Mock git status to show no changes
    mock_run.return_value = MagicMock(stdout="")
    
    git_ops = GitOperations(repo_path)
    with patch('builtins.print') as mock_print:
        result = git_ops.commit_and_push(file_path, "Test commit")
        assert result is True
        mock_print.assert_called_with("No changes to commit, skipping git operations")

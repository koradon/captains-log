"""Tests for the git module."""

import subprocess
from unittest.mock import MagicMock, patch

from src.git import CommitParser, GitOperations


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


@patch("subprocess.run")
def test_git_operations_has_changes_true(mock_run, tmp_path):
    """Test has_changes when changes exist."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)

    mock_run.return_value = MagicMock(stdout="M  file.txt")
    assert git_ops.has_changes() is True


@patch("subprocess.run")
def test_git_operations_has_changes_false(mock_run, tmp_path):
    """Test has_changes when no changes exist."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)

    mock_run.return_value = MagicMock(stdout="")
    assert git_ops.has_changes() is False


@patch("subprocess.run")
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


@patch("subprocess.run")
def test_git_operations_add_file_success(mock_run, tmp_path):
    """Test successful file addition."""
    repo_path = tmp_path / "repo"
    file_path = repo_path / "test.txt"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("test")

    git_ops = GitOperations(repo_path)
    assert git_ops.add_file(file_path) is True
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_git_operations_add_file_error(mock_run, tmp_path):
    """Test file addition error."""
    repo_path = tmp_path / "repo"
    file_path = repo_path / "test.txt"

    mock_run.side_effect = subprocess.CalledProcessError(1, "git")
    git_ops = GitOperations(repo_path)
    assert git_ops.add_file(file_path) is False


@patch("subprocess.run")
def test_git_operations_commit_success(mock_run, tmp_path):
    """Test successful commit."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)

    assert git_ops.commit("Test commit") is True
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_git_operations_commit_error(mock_run, tmp_path):
    """Test commit error."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)

    mock_run.side_effect = subprocess.CalledProcessError(1, "git")
    assert git_ops.commit("Test commit") is False


@patch("subprocess.run")
def test_git_operations_push_success(mock_run, tmp_path):
    """Test successful push."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)

    assert git_ops.push() is True
    mock_run.assert_called_once()


@patch("subprocess.run")
def test_git_operations_push_error(mock_run, tmp_path):
    """Test push error."""
    repo_path = tmp_path / "repo"
    git_ops = GitOperations(repo_path)

    mock_run.side_effect = subprocess.CalledProcessError(1, "git")
    assert git_ops.push() is False


@patch("subprocess.run")
def test_git_operations_commit_and_push_success(mock_run, tmp_path):
    """Test successful commit and push workflow."""
    repo_path = tmp_path / "repo"
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True)

    file_path = repo_path / "test.txt"
    file_path.write_text("test")

    # Mock git operations: status, add_all, commit, push
    mock_run.side_effect = [
        MagicMock(stdout="M  test.txt"),  # status - has changes
        MagicMock(),  # add_all
        MagicMock(),  # commit
        MagicMock(),  # push
    ]

    git_ops = GitOperations(repo_path)
    result = git_ops.commit_and_push("Test commit")

    assert result is True
    assert mock_run.call_count == 4


def test_git_operations_commit_and_push_lock_files(tmp_path):
    """Test commit and push with lock files present."""
    repo_path = tmp_path / "repo"
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "index.lock").write_text("")

    git_ops = GitOperations(repo_path)
    with patch("builtins.print") as mock_print:
        result = git_ops.commit_and_push("Test commit")
        assert result is False
        mock_print.assert_called_with(
            "Warning: Git lock files found, skipping operations"
        )


@patch("subprocess.run")
def test_git_operations_commit_and_push_no_changes(mock_run, tmp_path):
    """Test commit and push when no changes exist."""
    repo_path = tmp_path / "repo"
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True)

    # Mock git status to show no changes
    mock_run.return_value = MagicMock(stdout="")

    git_ops = GitOperations(repo_path)
    with patch("builtins.print") as mock_print:
        result = git_ops.commit_and_push("Test commit")
        assert result is True
        mock_print.assert_called_with("No changes to commit, skipping git operations")


@patch("subprocess.run")
def test_git_operations_add_all_success(mock_run, tmp_path):
    """Test successful add_all operation with .md files."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    git_ops = GitOperations(repo_path)

    # Mock git status to return .md files
    # Files are now batched together in a single git add call
    mock_run.side_effect = [
        MagicMock(stdout="M  test.md\nA  new.md"),  # status
        MagicMock(),  # batch add: test.md and new.md together
    ]
    assert git_ops.add_all() is True
    assert mock_run.call_count == 2
    # Verify status was called first
    mock_run.assert_any_call(
        ["git", "-C", str(repo_path), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    )
    # Verify .md files were added in batch
    add_calls = [call[0][0] for call in mock_run.call_args_list if "add" in call[0][0]]
    assert len(add_calls) == 1, "Should batch add files together"
    assert "test.md" in add_calls[0] and "new.md" in add_calls[0]


@patch("subprocess.run")
def test_git_operations_add_all_error(mock_run, tmp_path):
    """Test add_all error handling."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    git_ops = GitOperations(repo_path)

    # Mock git status to fail
    mock_run.side_effect = subprocess.CalledProcessError(1, "git")
    assert git_ops.add_all() is False


@patch("subprocess.run")
def test_git_operations_commit_and_push_uses_add_all(mock_run, tmp_path):
    """Test that commit_and_push uses add_all() which filters to .md files."""
    repo_path = tmp_path / "repo"
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True)

    # Create .md files to test add_all
    file1 = repo_path / "test1.md"
    file2 = repo_path / "test2.md"
    file1.write_text("test1")
    file2.write_text("test2")

    # Mock git operations: status (for has_changes), status (for add_all), batch add files, commit, push
    mock_run.side_effect = [
        MagicMock(stdout="M  test1.md\nM  test2.md"),  # status - has changes
        MagicMock(stdout="M  test1.md\nM  test2.md"),  # status - for add_all
        MagicMock(),  # batch add: test1.md and test2.md together
        MagicMock(),  # commit
        MagicMock(),  # push
    ]

    git_ops = GitOperations(repo_path)
    result = git_ops.commit_and_push("Test commit")

    assert result is True
    assert mock_run.call_count == 5

    # Verify add_all filtered to .md files and batched them together
    add_calls = [call[0][0] for call in mock_run.call_args_list if "add" in call[0][0]]
    assert len(add_calls) == 1, "Should batch add both .md files together"
    assert "test1.md" in add_calls[0] and "test2.md" in add_calls[0]


@patch("subprocess.run")
def test_git_operations_commit_and_push_add_all_failure(mock_run, tmp_path):
    """Test commit_and_push when add_all fails."""
    repo_path = tmp_path / "repo"
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True)

    # Mock git operations: status succeeds (for has_changes), status succeeds (for add_all), add fails
    mock_run.side_effect = [
        MagicMock(stdout="M  test.md"),  # status - has changes
        MagicMock(stdout="M  test.md"),  # status - for add_all
        subprocess.CalledProcessError(1, "git add"),  # add fails
    ]

    git_ops = GitOperations(repo_path)
    with patch("builtins.print") as mock_print:
        result = git_ops.commit_and_push("Test commit")
        assert result is False
        mock_print.assert_called_with("Warning: Failed to add files to git")


@patch("subprocess.run")
def test_git_operations_add_all_filters_non_md_files(mock_run, tmp_path):
    """Test that add_all only adds .md files and filters out other files."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    git_ops = GitOperations(repo_path)

    # Mock git status with mixed file types
    mock_run.side_effect = [
        MagicMock(
            stdout="M  test.md\nM  config.txt\nA  readme.md\n??  script.py"
        ),  # status
        MagicMock(),  # batch add: test.md and readme.md together
    ]
    assert git_ops.add_all() is True
    assert mock_run.call_count == 2

    # Verify only .md files were added (batched together)
    add_calls = [call[0][0] for call in mock_run.call_args_list if "add" in call[0][0]]
    assert len(add_calls) == 1, "Should batch add .md files together"
    # Check that both .md files are in the batch add call
    assert "test.md" in add_calls[0] and "readme.md" in add_calls[0]
    # Verify non-.md files were NOT added
    assert "config.txt" not in add_calls[0] and "script.py" not in add_calls[0]


@patch("subprocess.run")
def test_git_operations_add_all_includes_directories_with_md_files(mock_run, tmp_path):
    """Test that add_all includes directories containing .md files."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / "2024").mkdir()
    (repo_path / "2024" / "01").mkdir()
    (repo_path / "2024" / "01" / "2024.01.15.md").write_text("# Log")

    git_ops = GitOperations(repo_path)

    # Mock git status showing new directory with .md file
    # The code will add the file and all parent directories (2024/01 and 2024) in a batch
    mock_run.side_effect = [
        MagicMock(stdout="?? 2024/01/2024.01.15.md"),  # status
        MagicMock(),  # batch add: 2024/01/2024.01.15.md, 2024/01, and 2024 together
    ]
    assert git_ops.add_all() is True

    # Verify file and directories were added in batch
    add_calls = [call[0][0] for call in mock_run.call_args_list if "add" in call[0][0]]
    assert len(add_calls) == 1, "Should batch add file and directories together"
    assert "2024/01/2024.01.15.md" in add_calls[0]
    assert "2024/01" in add_calls[0]
    assert "2024" in add_calls[0]


@patch("subprocess.run")
def test_git_operations_add_all_handles_file_moves(mock_run, tmp_path):
    """Test that add_all handles file moves (renames) correctly."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    git_ops = GitOperations(repo_path)

    # Mock git status showing renamed file (R = renamed)
    # The code will add old path, new path, and parent directories in a batch
    mock_run.side_effect = [
        MagicMock(stdout="R  2024.01.15.md -> 2024/01/2024.01.15.md"),  # status
        MagicMock(),  # batch add: old path, new path, and directories together
    ]
    assert git_ops.add_all() is True

    # Verify both old and new paths were added, plus directories (batched)
    add_calls = [call[0][0] for call in mock_run.call_args_list if "add" in call[0][0]]
    assert len(add_calls) == 1, "Should batch add all paths together"
    assert "2024.01.15.md" in add_calls[0]
    assert "2024/01/2024.01.15.md" in add_calls[0]
    assert "2024/01" in add_calls[0]
    assert "2024" in add_calls[0]

"""Git operations for Captain's Log."""

import subprocess
from pathlib import Path


class GitOperations:
    """Handles git operations for the log repository."""

    def __init__(self, repo_path: Path):
        """Initialize with repository path.

        Args:
            repo_path: Path to the git repository
        """
        self.repo_path = repo_path

    def has_changes(self) -> bool:
        """Check if there are any uncommitted changes in the repository.

        Returns:
            True if there are changes, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False

    def has_lock_files(self) -> bool:
        """Check if there are any git lock files present.

        Returns:
            True if lock files exist, False otherwise
        """
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            return False

        lock_files = list(git_dir.glob("*.lock"))
        return len(lock_files) > 0

    def add_file(self, file_path: Path) -> bool:
        """Add a file to the git staging area.

        Args:
            file_path: Path to the file to add

        Returns:
            True if successful, False otherwise
        """
        try:
            relative_path = file_path.relative_to(self.repo_path)
            subprocess.run(
                ["git", "-C", str(self.repo_path), "add", str(relative_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except (subprocess.CalledProcessError, ValueError):
            return False

    def commit(self, message: str) -> bool:
        """Create a commit with the given message.

        Args:
            message: Commit message

        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ["git", "-C", str(self.repo_path), "commit", "-m", message],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def push(self) -> bool:
        """Push commits to the remote repository.

        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ["git", "-C", str(self.repo_path), "push"],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def commit_and_push(self, file_path: Path, commit_message: str) -> bool:
        """Perform the complete commit and push workflow.

        Args:
            file_path: Path to the file to commit
            commit_message: Commit message

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check for lock files
            if self.has_lock_files():
                print("Warning: Git lock files found, skipping operations")
                return False

            # Check if there are any changes to commit
            if not self.has_changes():
                print("No changes to commit, skipping git operations")
                return True

            # Add the file
            if not self.add_file(file_path):
                print(f"Warning: Failed to add file {file_path}")
                return False

            # Commit
            if not self.commit(commit_message):
                print("Warning: Failed to commit changes")
                return False

            # Push
            if not self.push():
                print("Warning: Failed to push changes")
                return False

            print("Successfully committed and pushed log updates")
            return True

        except Exception as e:
            print(f"Warning: Unexpected error during git operations: {e}")
            return False

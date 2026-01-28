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

    def add_all(self) -> bool:
        """Add all changes to the git staging area.

        Safeguard: Only adds .md files and directories containing .md files
        to prevent accidentally committing unwanted files.

        Note: git status --porcelain does NOT truncate output - it will return
        all files regardless of count. However, we batch add files to avoid
        command line length limits and improve performance with large file lists.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get list of changed files from git status
            # Note: git status --porcelain outputs all files (no truncation),
            # but subprocess.run with capture_output=True buffers all output in memory
            status_result = subprocess.run(
                ["git", "-C", str(self.repo_path), "status", "--porcelain"],
                check=True,
                capture_output=True,
                text=True,
            )

            if not status_result.stdout.strip():
                # No changes to add
                return True

            # Parse status output and filter to .md files and directories
            paths_to_add = set()

            for line in status_result.stdout.strip().split("\n"):
                if not line.strip():
                    continue

                # Git status format: XY filename
                # X = index status, Y = working tree status
                # Common values: M=modified, A=added, D=deleted, ??=untracked, R=renamed
                status = line[:2]
                file_path = line[3:].strip()

                # Handle renamed files (format: "R  old -> new")
                if "R" in status:
                    parts = file_path.split(" -> ")
                    if len(parts) == 2:
                        old_path, new_path = parts
                        # Add both old (for deletion) and new (for addition) if .md files
                        if old_path.endswith(".md"):
                            paths_to_add.add(old_path)
                        if new_path.endswith(".md"):
                            paths_to_add.add(new_path)
                            # Also add parent directories if file is in a subdirectory
                            new_path_obj = Path(self.repo_path) / new_path
                            parent = new_path_obj.parent
                            while parent != Path(self.repo_path):
                                paths_to_add.add(
                                    str(parent.relative_to(self.repo_path))
                                )
                                next_parent = parent.parent
                                if next_parent == parent:  # Reached filesystem root
                                    break
                                parent = next_parent
                    continue

                # Check if it's a .md file
                if file_path.endswith(".md"):
                    paths_to_add.add(file_path)
                    # If file is in a subdirectory, also add parent directories
                    file_path_obj = Path(self.repo_path) / file_path
                    parent = file_path_obj.parent
                    while parent != Path(self.repo_path):
                        paths_to_add.add(str(parent.relative_to(self.repo_path)))
                        next_parent = parent.parent
                        if next_parent == parent:  # Reached filesystem root
                            break
                        parent = next_parent
                # Check if it's a directory (untracked directories show up without extension)
                else:
                    path_obj = Path(self.repo_path) / file_path
                    if path_obj.is_dir():
                        # Check if directory contains any .md files
                        if any(f.suffix == ".md" for f in path_obj.rglob("*.md")):
                            paths_to_add.add(file_path)

            # Add all paths (files and directories)
            if paths_to_add:
                sorted_paths = sorted(paths_to_add)

                # Batch add files to avoid too many individual git commands
                # Git can handle adding multiple files at once, which is more efficient
                # However, we need to be careful about command line length limits
                # Typical limit is ~128KB on most systems, so we batch in chunks
                MAX_ARGS_LENGTH = 100000  # Conservative limit (~100KB)
                BATCH_SIZE = (
                    100  # Process files in batches to avoid command line limits
                )

                # Process in batches to avoid command line length limits
                for i in range(0, len(sorted_paths), BATCH_SIZE):
                    batch = sorted_paths[i : i + BATCH_SIZE]
                    # Estimate command length (rough approximation)
                    cmd_length = (
                        sum(len(str(p)) for p in batch) + 100
                    )  # +100 for git command overhead

                    if cmd_length > MAX_ARGS_LENGTH or len(batch) == 1:
                        # Add individually if batch would be too long or only one file
                        for path in batch:
                            subprocess.run(
                                ["git", "-C", str(self.repo_path), "add", path],
                                check=True,
                                capture_output=True,
                                text=True,
                            )
                    else:
                        # Batch add multiple files at once
                        subprocess.run(
                            ["git", "-C", str(self.repo_path), "add"] + batch,
                            check=True,
                            capture_output=True,
                            text=True,
                        )

            return True
        except subprocess.CalledProcessError:
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

    def commit_and_push(self, commit_message: str) -> bool:
        """Perform the complete commit and push workflow.

        Args:
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

            # Add all changes
            if not self.add_all():
                print("Warning: Failed to add files to git")
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

"""Commit parsing utilities for Captain's Log."""

from typing import Optional, Tuple


class CommitParser:
    """Handles parsing commit information and validation."""

    @staticmethod
    def is_valid_commit_sha(commit_sha: str) -> bool:
        """Check if a commit SHA is valid for logging.

        Args:
            commit_sha: The commit SHA to validate

        Returns:
            True if the SHA is valid for logging, False otherwise
        """
        if not commit_sha or commit_sha == "no-sha":
            return False

        if commit_sha.startswith("no-sha"):
            return False

        return True

    @staticmethod
    def parse_commit_entry(entry: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse a formatted commit entry to extract SHA and message.

        Args:
            entry: Entry in format "- (sha) message"

        Returns:
            Tuple of (sha, message) or (None, None) if parsing fails
        """
        if not entry.startswith("- (") or ") " not in entry:
            return None, None

        try:
            sha_end = entry.find(")")
            sha = entry[3:sha_end]
            message = entry[sha_end + 2 :]
            return sha, message
        except (ValueError, IndexError):
            return None, None

    @staticmethod
    def should_skip_commit(
        commit_sha: str, repo_path: str, global_log_repo: Optional[str]
    ) -> bool:
        """Determine if a commit should be skipped for logging.

        Args:
            commit_sha: The commit SHA
            repo_path: Path to the repository
            global_log_repo: Path to the global log repository

        Returns:
            True if the commit should be skipped, False otherwise
        """
        # Skip if commit SHA is invalid
        if not CommitParser.is_valid_commit_sha(commit_sha):
            return True

        # Skip if we're in the log repository itself to prevent infinite loops
        if global_log_repo:
            from pathlib import Path

            global_repo_abs = Path(global_log_repo).resolve()
            repo_path_abs = Path(repo_path).resolve()

            # Only skip if we're committing from within the actual log repository
            if repo_path_abs == global_repo_abs:
                return True

        return False

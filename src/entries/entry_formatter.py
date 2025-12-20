"""Entry formatting utilities for Captain's Log."""

from typing import List

from src.entries.entry_models import CommitEntry, ManualEntry


class EntryFormatter:
    """Handles formatting of different types of entries."""

    @staticmethod
    def format_commit_entry(sha: str, message: str) -> str:
        """Format a commit entry.

        Args:
            sha: Commit SHA
            message: Commit message

        Returns:
            Formatted entry string
        """
        entry = CommitEntry(sha=sha, message=message, repo_name="")
        return entry.format()

    @staticmethod
    def format_manual_entry(text: str) -> str:
        """Format a manual entry.

        Args:
            text: Entry text

        Returns:
            Formatted entry string
        """
        entry = ManualEntry(text=text)
        return entry.format()

    @staticmethod
    def format_entries_for_repo(repo_name: str, entries: List[str]) -> List[str]:
        """Format all entries for a repository section.

        Args:
            repo_name: Name of the repository
            entries: List of entry strings

        Returns:
            Formatted section as list of lines
        """
        if not entries:
            return []

        lines = [f"## {repo_name}"]
        lines.extend(entries)
        lines.append("")  # Empty line after section

        return lines

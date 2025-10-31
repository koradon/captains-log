"""Entry processing logic for Captain's Log."""

from typing import Dict, List

from src.entries.entry_formatter import EntryFormatter
from src.entries.entry_models import CommitEntry


class EntryProcessor:
    """Handles processing and updating of log entries."""

    def __init__(self):
        """Initialize the entry processor."""
        self.formatter = EntryFormatter()

    def update_commit_entries(
        self, entries: List[str], new_sha: str, new_message: str
    ) -> List[str]:
        """Update commit entries list with new commit, handling duplicates.

        Args:
            entries: Current list of formatted entries
            new_sha: New commit SHA
            new_message: New commit message

        Returns:
            Updated list of entries
        """
        # Use short SHA (first 7 characters)
        short_sha = new_sha[:7] if len(new_sha) >= 7 else new_sha

        # Find entries with the same message but different SHA to remove
        to_remove = []
        for i, entry in enumerate(entries):
            parsed = CommitEntry.parse(entry)
            if parsed and parsed.message == new_message and parsed.sha != short_sha:
                to_remove.append(i)
            elif parsed and parsed.sha == short_sha and parsed.message == new_message:
                # Exact match already exists, no need to add
                return entries

        # Remove outdated entries (in reverse order to maintain indices)
        for i in reversed(to_remove):
            entries.pop(i)

        # Add the new entry
        new_entry = self.formatter.format_commit_entry(new_sha, new_message)
        entries.append(new_entry)

        return entries

    def add_manual_entry(self, entries: List[str], entry_text: str) -> List[str]:
        """Add a manual entry to the entries list.

        Args:
            entries: Current list of formatted entries
            entry_text: Text for the manual entry

        Returns:
            Updated list of entries
        """
        # Create a copy to avoid mutating the original list
        updated_entries = entries.copy()
        new_entry = self.formatter.format_manual_entry(entry_text)

        # Check if entry already exists to avoid duplicates
        if new_entry not in updated_entries:
            updated_entries.append(new_entry)

        return updated_entries

    def organize_repos_for_output(
        self, repos: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Organize repositories for output with optional 'other' section placement.

        Args:
            repos: Dictionary of repo names to entry lists

        Returns:
            Ordered dictionary ready for output
        """
        # Custom sorting with 'other' at the end
        other_entries = repos.pop("other", None)
        sorted_repos = dict(sorted(repos.items(), key=lambda x: x[0].lower()))

        if other_entries is not None:
            sorted_repos["other"] = other_entries

        return sorted_repos

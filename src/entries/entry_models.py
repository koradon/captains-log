"""Entry data models for Captain's Log."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CommitEntry:
    """Represents a commit-based log entry."""

    sha: str
    message: str
    repo_name: str

    @property
    def short_sha(self) -> str:
        """Get the short version of the SHA (first 7 characters)."""
        return self.sha[:7] if len(self.sha) >= 7 else self.sha

    def format(self) -> str:
        """Format the entry as a markdown list item."""
        return f"- ({self.short_sha}) {self.message}"

    @classmethod
    def parse(cls, formatted_entry: str) -> Optional["CommitEntry"]:
        """Parse a formatted entry back to CommitEntry.

        Args:
            formatted_entry: Entry in format "- (sha) message"

        Returns:
            CommitEntry if parsing succeeds, None otherwise
        """
        if not formatted_entry.startswith("- (") or ") " not in formatted_entry:
            return None

        try:
            sha_end = formatted_entry.find(")")
            sha = formatted_entry[3:sha_end]
            message = formatted_entry[sha_end + 2 :]

            return cls(sha=sha, message=message, repo_name="")
        except (ValueError, IndexError):
            return None


@dataclass
class ManualEntry:
    """Represents a manually added log entry."""

    text: str
    category: str = "other"

    def format(self) -> str:
        """Format the entry as a markdown list item."""
        return f"- {self.text}"

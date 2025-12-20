"""Log file writing functionality for Captain's Log."""

from pathlib import Path

from src.entries.entry_processor import EntryProcessor
from src.logs.log_models import LogData


class LogWriter:
    """Handles writing log data to markdown files."""

    # Default log file structure
    HEADER = "# What I did\n\n"
    FOOTER = "# Whats next\n\n\n# What Broke or Got Weird\n"

    def __init__(self):
        """Initialize the log writer."""
        self.entry_processor = EntryProcessor()

    def write_log_file(self, file_path: Path, log_data: LogData):
        """Write log data to a markdown file.

        Args:
            file_path: Path where to write the log file
            log_data: Log data to write
        """
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create file with basic structure if it doesn't exist
            if not file_path.exists():
                with file_path.open("w", encoding="utf-8") as f:
                    f.write(self.HEADER)
                    f.write("\n\n")
                    f.write(self.FOOTER)

            # Read existing content to preserve footer
            try:
                content = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                # If we can't read the file, start fresh
                content = self.HEADER + "\n\n" + self.FOOTER

            # Ensure we have proper structure
            if "# What I did" not in content:
                content = self.HEADER + "\n\n" + self.FOOTER

            # Organize repositories for output (What I did section)
            organized_repos = self.entry_processor.organize_repos_for_output(
                log_data.repos
            )

            # Generate content lines for "What I did" section
            content_lines = []
            for repo_name, entries in organized_repos.items():
                if entries:  # Only include repos with entries
                    content_lines.append(f"## {repo_name}")
                    content_lines.extend(entries)
                    content_lines.append("")  # Empty line after section

            # Construct final content
            what_i_did_content = (
                "\n".join(content_lines).rstrip() if content_lines else ""
            )

            # Build the complete log structure
            new_content = self.HEADER
            if what_i_did_content:
                new_content += what_i_did_content + "\n\n"
            else:
                new_content += "\n"

            # Add the "Whats next" section
            new_content += "# Whats next\n\n\n"

            # Add the "What Broke or Got Weird" section with flat list
            new_content += "# What Broke or Got Weird\n"
            if log_data.what_broke:
                new_content += "\n"
                for entry in log_data.what_broke:
                    new_content += entry + "\n"
            else:
                new_content += "\n"

            # Write atomically to avoid corruption
            temp_file = file_path.with_suffix(file_path.suffix + ".tmp")
            temp_file.write_text(new_content, encoding="utf-8")
            temp_file.replace(file_path)

        except Exception as e:
            print(f"Error saving log file {file_path}: {e}")
            raise

    def get_log_template(self) -> str:
        """Get the basic log file template.

        Returns:
            Basic log file template as string
        """
        return self.HEADER + "\n" + self.FOOTER

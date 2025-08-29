"""Log file writing functionality for Captain's Log."""

from pathlib import Path
from typing import Dict, List

from logs.log_models import LogData
from entries.entry_processor import EntryProcessor


class LogWriter:
    """Handles writing log data to markdown files."""
    
    # Default log file structure
    HEADER = "# What I did\n\n"
    FOOTER = "# Whats next\n\n\n# What Broke or Got Weird\n"
    
    def __init__(self, other_at_end: bool = False):
        """Initialize the log writer.
        
        Args:
            other_at_end: Whether to place 'other' section at the end
        """
        self.other_at_end = other_at_end
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
            except (UnicodeDecodeError, IOError):
                # If we can't read the file, start fresh
                content = self.HEADER + "\n\n" + self.FOOTER
            
            # Ensure we have proper structure
            if "# What I did" not in content:
                content = self.HEADER + "\n\n" + self.FOOTER
            
            # Split content to preserve footer
            parts = content.split(self.FOOTER, 1)
            footer_part = self.FOOTER
            
            # Organize repositories for output
            organized_repos = self.entry_processor.organize_repos_for_output(
                log_data.repos, self.other_at_end
            )
            
            # Generate content lines
            content_lines = []
            for repo_name, entries in organized_repos.items():
                if entries:  # Only include repos with entries
                    content_lines.append(f"## {repo_name}")
                    content_lines.extend(entries)
                    content_lines.append("")  # Empty line after section
            
            # Construct final content
            if content_lines:
                new_content = self.HEADER + "\n".join(content_lines).rstrip() + "\n\n" + footer_part
            else:
                new_content = self.HEADER + "\n" + footer_part
            
            # Write atomically to avoid corruption
            temp_file = file_path.with_suffix(file_path.suffix + '.tmp')
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

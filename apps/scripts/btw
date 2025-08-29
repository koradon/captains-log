#!/usr/bin/env python3
"""
BTW (By The Way) - Quick log entry tool for Captain's Log

Usage: btw "What I have done"

This adds an entry to today's daily log under a "What I did" section,
using "other" as the category instead of a repository name.
"""

import sys
import os
from pathlib import Path
from datetime import date
import yaml

# Add the src directory to Python path so we can import the main functions
CAPTAINS_LOG_DIR = Path.home() / ".captains-log"
SRC_DIR = CAPTAINS_LOG_DIR.parent / "captains-log" / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

# Try to import from installed location first, then from src
try:
    from update_log import load_config, get_log_repo_and_path, load_log, commit_and_push, find_project
    # Import constants for custom save function
    from update_log import HEADER, FOOTER
except ImportError:
    # If not installed, try to import from current directory structure
    script_dir = Path(__file__).parent.parent.parent
    src_dir = script_dir / "src"
    if src_dir.exists():
        sys.path.insert(0, str(src_dir))
        from update_log import load_config, get_log_repo_and_path, load_log, commit_and_push, find_project
        from update_log import HEADER, FOOTER
    else:
        print("Error: Cannot find Captain's Log modules. Please ensure Captain's Log is properly installed.")
        sys.exit(1)

def save_log_with_other_at_end(file_path, repos):
    """Custom save function that places 'other' section at the end."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if not file_path.exists():
            with file_path.open("w", encoding="utf-8") as f:
                f.write(HEADER)
                f.write("\n\n")
                f.write(FOOTER)

        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IOError):
            # If we can't read the file, start fresh
            content = HEADER + "\n\n" + FOOTER

        if "# What I did" not in content:
            content = HEADER + "\n\n" + FOOTER
        parts = content.split(FOOTER, 1)
        main_part = parts[0].strip()
        footer_part = FOOTER

        commit_lines = []
        
        # First, add all sections except 'other' in alphabetical order
        other_entries = None
        sorted_repos = []
        for repo_name in sorted(repos.keys(), key=str.lower):
            if repo_name == "other":
                other_entries = repos[repo_name]
            else:
                sorted_repos.append(repo_name)
        
        # Add regular repository sections
        for repo in sorted_repos:
            commit_lines.append(f"## {repo}")
            commit_lines.extend(repos[repo])
            commit_lines.append("")
        
        # Add 'other' section at the end if it exists
        if other_entries is not None:
            commit_lines.append("## other")
            commit_lines.extend(other_entries)
            commit_lines.append("")

        new_content = HEADER + "\n".join(commit_lines).strip() + "\n\n" + footer_part
        
        # Write with atomic operation to avoid corruption
        temp_file = file_path.with_suffix(file_path.suffix + '.tmp')
        temp_file.write_text(new_content, encoding="utf-8")
        temp_file.replace(file_path)
        
    except Exception as e:
        print(f"Error saving log file {file_path}: {e}")
        raise

def add_manual_entry(entry_text):
    """Add a manual entry to the daily log under 'other' category."""
    config = load_config()
    
    # Use current working directory to determine project using the same logic as update_log.py
    cwd = Path.cwd()
    project = find_project(str(cwd), config)
    
    log_repo_path, log_file = get_log_repo_and_path(project, config)
    
    # Load existing log
    repos = load_log(log_file)
    
    # Add entry under "other" category
    category = "other"
    if category not in repos:
        repos[category] = []
    
    # Format the entry (without commit hash since this is manual)
    formatted_entry = f"- {entry_text}"
    
    # Check if entry already exists to avoid duplicates
    if formatted_entry not in repos[category]:
        repos[category].append(formatted_entry)
        
        # Save the updated log with 'other' at the end
        save_log_with_other_at_end(log_file, repos)
        
        # Commit and push if we have a log repository
        if log_repo_path is not None:
            commit_and_push(log_repo_path, log_file, f"Add manual entry to {project} logs for {date.today().isoformat()}")
        
        print(f"Added entry to {project} log: {entry_text}")
    else:
        print(f"Entry already exists in {project} log: {entry_text}")

def main():
    if len(sys.argv) < 2:
        print("Usage: btw \"What I have done\"")
        print("Example: btw \"Reviewed the new API documentation\"")
        sys.exit(1)
    
    # Join all arguments to allow for entries without quotes
    entry_text = " ".join(sys.argv[1:])
    
    if not entry_text.strip():
        print("Error: Entry text cannot be empty")
        sys.exit(1)
    
    try:
        add_manual_entry(entry_text)
    except Exception as e:
        print(f"Error adding entry: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

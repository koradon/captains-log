#!/usr/bin/env python3
"""
Test script for the wnext command functionality.

This script tests that:
1. Entries are added to the "Whats next" section
2. Entries are grouped under the correct subsection
3. Log structure (headers) is preserved correctly
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.config_models import Config, ProjectConfig  # type: ignore  # noqa: E402
from entries import EntryProcessor  # type: ignore  # noqa: E402
from logs import LogData, LogManager, LogParser  # type: ignore  # noqa: E402
from projects.project_models import ProjectInfo  # type: ignore  # noqa: E402


def test_wnext_functionality():
    """Test that 'Whats next' entries are added to the correct sections."""
    print("Testing wnext functionality...")

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        log_dir = tmpdir_path / "logs"
        log_dir.mkdir()

        # Create a test config
        config = Config(
            global_log_repo=log_dir,
            projects={"test-project": ProjectConfig(root=tmpdir_path)},
        )

        # Create a test project
        project = ProjectInfo(
            name="test-project",
            config=ProjectConfig(root=tmpdir_path),
            base_dir=tmpdir_path,
        )

        # Initialize log manager
        log_manager = LogManager(config)
        log_info = log_manager.get_log_file_info(project)

        # Start with empty log data
        log_data = LogData()

        # Simulate wnext-style behavior: add a "Whats next" entry
        entry_processor = EntryProcessor()
        section_name = project.name

        existing_next = log_data.get_what_next_entries(section_name)
        updated_next = entry_processor.add_manual_entry(
            existing_next, "Test what next entry: plan tomorrow"
        )
        log_data.set_what_next_entries(section_name, updated_next)

        # Simulate wnext --other: add an entry under the "other" subsection
        existing_next_other = log_data.get_what_next_entries("other")
        updated_next_other = entry_processor.add_manual_entry(
            existing_next_other, "Test what next entry: miscellaneous task"
        )
        log_data.set_what_next_entries("other", updated_next_other)

        # Also add a regular "What I did" entry to ensure structure is intact
        existing_repo_entries = log_data.get_repo_entries("other")
        updated_repo_entries = entry_processor.add_manual_entry(
            existing_repo_entries, "Test regular entry for today"
        )
        log_data.set_repo_entries("other", updated_repo_entries)

        # Save the log
        log_manager.save_log(log_info, log_data)

        # Verify the file was created
        assert log_info.file_path.exists(), "Log file was not created"

        # Read and print content
        content = log_info.file_path.read_text()
        print("\nGenerated log file content (wnext):")
        print("=" * 60)
        print(content)
        print("=" * 60)

        # Parse the log file back
        parsed_data = LogParser.parse_log_file(log_info.file_path)

        # Verify headers
        assert "# What I did" in content, "Missing 'What I did' header"
        assert "# Whats next" in content, "Missing 'Whats next' header"
        assert "# What Broke or Got Weird" in content, "Missing 'What Broke' header"

        # Verify entries are in correct sections
        what_i_did_entries = parsed_data.get_repo_entries("other")
        what_next_entries = parsed_data.get_what_next_entries(section_name)
        what_next_other_entries = parsed_data.get_what_next_entries("other")

        print("\nWhat I did entries:", what_i_did_entries)
        print("Whats next entries (project):", what_next_entries)
        print("Whats next entries (other):", what_next_other_entries)

        assert len(what_i_did_entries) == 1, "Should have 1 entry in 'What I did'"
        assert len(what_next_entries) == 1, (
            "Should have 1 entry in project 'Whats next' subsection"
        )
        assert len(what_next_other_entries) == 1, (
            "Should have 1 entry in 'other' Whats next subsection"
        )
        assert "Test regular entry for today" in what_i_did_entries[0], (
            "Regular entry not found in 'What I did'"
        )
        assert "Test what next entry: plan tomorrow" in what_next_entries[0], (
            "'Whats next' entry not found in project 'Whats next' section"
        )
        assert (
            "Test what next entry: miscellaneous task" in what_next_other_entries[0]
        ), "'Whats next' entry not found in 'other' Whats next subsection"

        print("\n✅ All wnext tests passed!")
        return True


if __name__ == "__main__":
    try:
        test_wnext_functionality()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

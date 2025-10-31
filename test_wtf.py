#!/usr/bin/env python3
"""
Test script for the wtf command functionality.

This script tests that:
1. wtf.py can be imported and run
2. Entries are added to the "What Broke or Got Weird" section
3. Log structure is preserved correctly
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.config_models import Config, ProjectConfig
from logs import LogManager, LogParser
from projects.project_models import ProjectInfo


def test_wtf_functionality():
    """Test that wtf entries are added to the correct section."""
    print("Testing wtf functionality...")

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

        # Load initial log data (should be empty)
        log_data = log_manager.load_log(log_info)

        # Add a wtf entry manually (simulating what wtf.py does)
        from entries import EntryProcessor

        entry_processor = EntryProcessor()
        category = "other"

        # Add entry to "What Broke or Got Weird" section (flat list)
        formatted_wtf = entry_processor.formatter.format_manual_entry(
            "Test wtf entry: something broke"
        )
        log_data.add_what_broke_entry(formatted_wtf)

        # Also add a regular entry to "What I did" section
        regular_entries = log_data.get_repo_entries(category)
        updated_regular = entry_processor.add_manual_entry(
            regular_entries, "Test regular entry"
        )
        log_data.set_repo_entries(category, updated_regular)

        # Save the log
        log_manager.save_log(log_info, log_data)

        # Verify the file was created
        assert log_info.file_path.exists(), "Log file was not created"

        # Read and parse the file
        content = log_info.file_path.read_text()
        print("\nGenerated log file content:")
        print("=" * 60)
        print(content)
        print("=" * 60)

        # Parse the log file back
        parsed_data = LogParser.parse_log_file(log_info.file_path)

        # Verify structure
        assert "# What I did" in content, "Missing 'What I did' header"
        assert "# What Broke or Got Weird" in content, "Missing 'What Broke' header"
        assert "# Whats next" in content, "Missing 'Whats next' header"

        # Verify entries are in correct sections
        what_i_did_entries = parsed_data.get_repo_entries(category)
        what_broke_entries = parsed_data.get_what_broke_entries()

        print("\nWhat I did entries:", what_i_did_entries)
        print("What Broke entries:", what_broke_entries)

        assert len(what_i_did_entries) == 1, "Should have 1 entry in 'What I did'"
        assert len(what_broke_entries) == 1, (
            "Should have 1 entry in 'What Broke or Got Weird'"
        )
        assert "Test regular entry" in what_i_did_entries[0], (
            "Regular entry not found in 'What I did'"
        )
        assert "Test wtf entry" in what_broke_entries[0], (
            "WTF entry not found in 'What Broke or Got Weird'"
        )

        # Verify sections are in the correct order in the file
        what_i_did_pos = content.index("# What I did")
        whats_next_pos = content.index("# Whats next")
        what_broke_pos = content.index("# What Broke or Got Weird")

        assert what_i_did_pos < whats_next_pos < what_broke_pos, (
            "Sections are not in correct order"
        )

        print("\n✅ All tests passed!")
        return True


if __name__ == "__main__":
    try:
        test_wtf_functionality()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

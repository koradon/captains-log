#!/usr/bin/env python3
"""Tests for the wnext command functionality."""

from src.config.config_models import Config, ProjectConfig
from src.entries import EntryProcessor
from src.logs import LogData, LogManager, LogParser
from src.projects.project_models import ProjectInfo


def test_wnext_writes_to_whats_next_section(tmp_path, monkeypatch):
    """Ensure that 'Whats next' entries are written and parsed correctly."""
    # Arrange configuration and project
    log_dir = tmp_path / "logs"
    log_dir.mkdir()

    config = Config(
        global_log_repo=log_dir,
        projects={"test-project": ProjectConfig(root=tmp_path)},
    )

    project = ProjectInfo(
        name="test-project",
        config=ProjectConfig(root=tmp_path),
        base_dir=tmp_path,
    )

    manager = LogManager(config)
    log_info = manager.get_log_file_info(project)

    # Start with empty log data and a single What Next entry
    log_data = LogData()
    processor = EntryProcessor()
    section_name = project.name
    existing = log_data.get_what_next_entries(section_name)
    updated = processor.add_manual_entry(existing, "Plan next sprint")
    log_data.set_what_next_entries(section_name, updated)

    # Act: save and reload via parser
    manager.save_log(log_info, log_data)

    assert log_info.file_path.exists()
    parsed = LogParser.parse_log_file(log_info.file_path)

    assert parsed.what_next == {section_name: ["- Plan next sprint"]}
    content = log_info.file_path.read_text()
    assert "# Whats next" in content
    assert f"## {section_name}" in content
    assert "- Plan next sprint" in content

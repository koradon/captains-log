"""Tests for the entries module."""

from src.entries import CommitEntry, EntryFormatter, EntryProcessor, ManualEntry


# CommitEntry tests
def test_commit_entry_short_sha():
    """Test short SHA property."""
    entry = CommitEntry(sha="abcdef1234567890", message="Test", repo_name="test")
    assert entry.short_sha == "abcdef1"

    # Short SHA
    entry_short = CommitEntry(sha="abc", message="Test", repo_name="test")
    assert entry_short.short_sha == "abc"


def test_commit_entry_format():
    """Test formatting commit entry."""
    entry = CommitEntry(sha="abcdef1234567890", message="Test commit", repo_name="test")
    assert entry.format() == "- (abcdef1) Test commit"


def test_commit_entry_parse_valid():
    """Test parsing valid commit entry."""
    entry_str = "- (abc1234) This is a commit message"
    entry = CommitEntry.parse(entry_str)

    assert entry is not None
    assert entry.sha == "abc1234"
    assert entry.message == "This is a commit message"


def test_commit_entry_parse_invalid():
    """Test parsing invalid commit entry."""
    invalid_entries = [
        "This is not a commit entry",
        "- Not a commit",
        "- (abc1234",  # Missing closing paren
        "- abc1234) Missing opening paren",
    ]

    for invalid in invalid_entries:
        entry = CommitEntry.parse(invalid)
        assert entry is None


def test_commit_entry_parse_empty_message():
    """Test parsing commit entry with empty message."""
    entry_str = "- (abc1234) "
    entry = CommitEntry.parse(entry_str)

    assert entry is not None
    assert entry.sha == "abc1234"
    assert entry.message == ""


# ManualEntry tests
def test_manual_entry_format():
    """Test formatting manual entry."""
    entry = ManualEntry(text="Did some work")
    assert entry.format() == "- Did some work"


def test_manual_entry_category_default():
    """Test default category."""
    entry = ManualEntry(text="Test")
    assert entry.category == "other"


def test_manual_entry_category_custom():
    """Test custom category."""
    entry = ManualEntry(text="Test", category="custom")
    assert entry.category == "custom"


# EntryFormatter tests
def test_entry_formatter_format_commit_entry():
    """Test formatting commit entry."""
    result = EntryFormatter.format_commit_entry("abcdef1234567890", "Test commit")
    assert result == "- (abcdef1) Test commit"


def test_entry_formatter_format_manual_entry():
    """Test formatting manual entry."""
    result = EntryFormatter.format_manual_entry("Did some work")
    assert result == "- Did some work"


def test_entry_formatter_format_entries_for_repo():
    """Test formatting entries for repository section."""
    entries = ["- (abc123) First commit", "- (def456) Second commit"]
    result = EntryFormatter.format_entries_for_repo("test-repo", entries)

    expected = [
        "## test-repo",
        "- (abc123) First commit",
        "- (def456) Second commit",
        "",
    ]
    assert result == expected


def test_entry_formatter_format_entries_for_repo_empty():
    """Test formatting empty entries list."""
    result = EntryFormatter.format_entries_for_repo("test-repo", [])
    assert result == []


# EntryProcessor tests
def test_entry_processor_update_commit_entries_new_entry():
    """Test adding new commit entry."""
    processor = EntryProcessor()
    entries = ["- (abc123) Old commit"]

    result = processor.update_commit_entries(entries, "def456789", "New commit")
    expected = ["- (abc123) Old commit", "- (def4567) New commit"]
    assert result == expected


def test_entry_processor_update_commit_entries_duplicate_message():
    """Test removing duplicate message entries."""
    processor = EntryProcessor()
    entries = [
        "- (abc123) Same message",
        "- (def456) Another commit",
        "- (ghi789) Same message",
    ]

    result = processor.update_commit_entries(entries, "jkl012", "Same message")
    expected = ["- (def456) Another commit", "- (jkl012) Same message"]
    assert result == expected


def test_entry_processor_update_commit_entries_exact_match():
    """Test when exact SHA and message already exist."""
    processor = EntryProcessor()
    entries = ["- (abc123) Existing message"]

    result = processor.update_commit_entries(entries, "abc123", "Existing message")
    assert result == entries  # Should not change


def test_entry_processor_add_manual_entry():
    """Test adding manual entry."""
    processor = EntryProcessor()
    entries = ["- (abc123) Commit entry"]

    result = processor.add_manual_entry(entries, "Manual work done")
    expected = ["- (abc123) Commit entry", "- Manual work done"]
    assert result == expected


def test_entry_processor_add_manual_entry_duplicate():
    """Test adding duplicate manual entry."""
    processor = EntryProcessor()
    entries = ["- Manual work done"]

    result = processor.add_manual_entry(entries, "Manual work done")
    assert result == entries  # Should not change


def test_entry_processor_organize_repos_for_output_normal():
    """Test organizing repos without special 'other' handling."""
    processor = EntryProcessor()
    repos = {"zebra": ["- Entry 1"], "alpha": ["- Entry 2"], "beta": ["- Entry 3"]}

    result = processor.organize_repos_for_output(repos)
    expected_order = ["alpha", "beta", "zebra"]
    assert list(result.keys()) == expected_order


def test_entry_processor_organize_repos_for_output_other_at_end():
    """Test organizing repos with 'other' at the end."""
    processor = EntryProcessor()
    repos = {
        "zebra": ["- Entry 1"],
        "other": ["- Manual entry"],
        "alpha": ["- Entry 2"],
    }

    result = processor.organize_repos_for_output(repos)
    expected_order = ["alpha", "zebra", "other"]
    assert list(result.keys()) == expected_order


def test_entry_processor_organize_repos_for_output_no_other():
    """Test organizing repos when 'other' doesn't exist."""
    processor = EntryProcessor()
    repos = {"zebra": ["- Entry 1"], "alpha": ["- Entry 2"]}

    result = processor.organize_repos_for_output(repos)
    expected_order = ["alpha", "zebra"]
    assert list(result.keys()) == expected_order

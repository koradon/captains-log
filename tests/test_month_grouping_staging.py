"""Regression tests for month-boundary grouping and publication staging."""

import subprocess

import pytest

from src.git import GitOperations


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )


def init_log_repo(tmp_path):
    repo = tmp_path / "logs"
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", "--initial-branch=main", str(remote))
    git(tmp_path, "init", "--initial-branch=main", str(repo))
    git(repo, "config", "user.email", "sandbox@example.invalid")
    git(repo, "config", "user.name", "Sandbox")
    (repo / ".gitattributes").write_text("*.md merge=union\n")
    git(repo, "add", ".gitattributes")
    git(repo, "commit", "-m", "Seed")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    return repo


def leave_half_finished_grouping(repo, project="tripper"):
    project_dir = repo / project
    project_dir.mkdir(exist_ok=True)
    old_one = project_dir / "2026.10.01.md"
    old_two = project_dir / "2026.10.02.md"
    old_one.write_text("# Day one\n")
    old_two.write_text("# Day two\n")
    git(repo, "add", str(old_one.relative_to(repo)), str(old_two.relative_to(repo)))
    git(repo, "commit", "-m", "Track October logs")

    target_dir = project_dir / "2026" / "10"
    target_dir.mkdir(parents=True)
    new_one = target_dir / old_one.name
    new_two = target_dir / old_two.name
    old_one.rename(new_one)
    old_two.rename(new_two)

    git(repo, "add", str(new_one.relative_to(repo)))
    git(repo, "rm", "--cached", str(old_one.relative_to(repo)))
    assert "R " in git(repo, "status", "--porcelain").stdout

    spaced_old = project_dir / "notes with spaces.md"
    spaced_new = target_dir / spaced_old.name
    spaced_old.write_text("# Spaced\n")
    git(repo, "add", str(spaced_old.relative_to(repo)))
    git(repo, "commit", "-m", "Spaced path")
    spaced_old.rename(spaced_new)
    git(repo, "add", str(spaced_new.relative_to(repo)))
    git(repo, "rm", "--cached", str(spaced_old.relative_to(repo)))


@pytest.fixture
def log_repo(tmp_path):
    return init_log_repo(tmp_path)


def test_add_all_does_not_git_add_missing_rename_source(log_repo):
    leave_half_finished_grouping(log_repo)

    ops = GitOperations(log_repo)
    before = git(log_repo, "rev-parse", "HEAD").stdout.strip()

    assert ops.add_all() is True
    assert ops.commit("Organize logs") is True

    assert git(log_repo, "rev-parse", "HEAD").stdout.strip() != before
    assert not git(log_repo, "status", "--porcelain").stdout.strip()


def test_commit_and_push_finishes_staged_renames_and_unstaged_deletions(log_repo):
    leave_half_finished_grouping(log_repo)
    (log_repo / "tripper" / "2026.11.01.md").write_text("# Current month\n")

    ops = GitOperations(log_repo)

    assert ops.commit_and_push("Publish after grouping") is True
    assert not git(log_repo, "status", "--porcelain").stdout.strip()
    assert (log_repo / "tripper" / "2026" / "10" / "2026.10.01.md").exists()


def test_one_bad_add_path_does_not_abort_other_staging(log_repo, monkeypatch):
    project_dir = log_repo / "tripper"
    project_dir.mkdir(exist_ok=True)
    good = project_dir / "2026.11.01.md"
    good.write_text("# Good\n")
    git(log_repo, "add", "tripper/2026.11.01.md")
    git(log_repo, "commit", "-m", "Good file")
    (project_dir / "broken.md").write_text("# Broken\n")

    ops = GitOperations(log_repo)
    original_stage_add = ops._stage_add_path

    def flaky_add(relative_path):
        if relative_path == "tripper/broken.md":
            return False
        return original_stage_add(relative_path)

    monkeypatch.setattr(ops, "_stage_add_path", flaky_add)

    assert ops.add_all() is False
    assert git(log_repo, "status", "--porcelain").stdout.strip()

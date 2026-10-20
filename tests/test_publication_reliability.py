"""Incident regressions using only temporary homes and local Git remotes."""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from src import cli
from src.git import GitOperations

WORKSPACE = Path(__file__).resolve().parents[1]


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    hooks = tmp_path / "disabled-hooks"
    hooks.mkdir()
    for key in list(os.environ):
        if key.startswith(("GIT_", "CAPTAINS_LOG_")):
            monkeypatch.delenv(key)
    for key, value in {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.hooksPath",
        "GIT_CONFIG_VALUE_0": str(hooks),
        "GIT_AUTHOR_NAME": "Sandbox",
        "GIT_COMMITTER_NAME": "Sandbox",
        "GIT_AUTHOR_EMAIL": "sandbox@example.invalid",
        "GIT_COMMITTER_EMAIL": "sandbox@example.invalid",
        "GIT_ALLOW_PROTOCOL": "file",
        "PYTHONPATH": str(WORKSPACE),
    }.items():
        monkeypatch.setenv(key, value)
    remote, logs, source = (
        tmp_path / name for name in ("remote.git", "logs", "source")
    )
    git(tmp_path, "init", "--bare", "--initial-branch=main", str(remote))
    git(tmp_path, "clone", str(remote), str(logs))
    (logs / ".gitattributes").write_text("*.md merge=union\n")
    git(logs, "add", ".gitattributes")
    git(logs, "commit", "-m", "Seed logs")
    git(logs, "push", "-u", "origin", "main")
    git(tmp_path, "init", "--initial-branch=main", str(source))
    git(source, "commit", "--allow-empty", "-m", "Source seed")
    config = home / ".captains-log" / "config.yml"
    config.parent.mkdir()
    config.write_text(f"global_log_repo: {logs}\nprojects: {{}}\n")
    return home, remote, logs, source


def test_abandoned_lock_recovery_publishes_all_pending_files(
    sandbox, monkeypatch, capsys
):
    from src import update_log
    from src.config.config_loader import set_config_path

    home, remote, logs, source = sandbox
    set_config_path(home / ".captains-log" / "config.yml")
    lock = logs / ".git" / "index.lock"
    lock.touch()
    # Simulate the passage of two days, including ctime, without altering real clocks.
    future = time.time() + 2 * 24 * 60 * 60
    monkeypatch.setattr("src.git.git_operations.time.time", lambda: future)
    monkeypatch.setattr(GitOperations, "LOCK_RETRY_DELAY", 0)
    monkeypatch.setattr("src.git.git_operations.shutil.which", lambda _: "test-lsof")
    original_run = subprocess.run

    def no_holder(args, **kwargs):
        if args[0] == "test-lsof":
            assert Path(args[-1]) == lock
            return subprocess.CompletedProcess(args, 1, "", "")
        return original_run(args, **kwargs)

    monkeypatch.setattr("src.git.git_operations.subprocess.run", no_holder)
    (logs / "earlier.md").write_text("Earlier pending entry\n")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "update_log",
            source.name,
            str(source),
            git(source, "rev-parse", "HEAD"),
            "Recovery entry",
        ],
    )

    update_log.main()

    assert not lock.exists()
    assert "Recovered abandoned Git lock" in capsys.readouterr().out
    assert "Earlier pending entry" in git(remote, "show", "main:earlier.md")
    assert "Recovery entry" in git(remote, "grep", "Recovery entry", "main")


def test_old_lock_with_open_owner_is_preserved(sandbox, monkeypatch):
    if shutil.which("lsof") is None or os.name != "posix":
        pytest.skip("Real ownership inspection requires POSIX lsof")
    _, _, logs, _ = sandbox
    lock = logs / ".git" / "index.lock"
    lock.touch()
    future = time.time() + 2 * 24 * 60 * 60
    monkeypatch.setattr("src.git.git_operations.time.time", lambda: future)
    monkeypatch.setattr(GitOperations, "LOCK_RETRY_DELAY", 0)
    ops = GitOperations(logs)

    with lock.open():
        ready = ops.wait_for_locks()

    assert ready is False
    assert lock.exists()


@pytest.mark.parametrize("evidence", ["missing", "error", "timeout", "changed"])
def test_uncertain_lock_ownership_never_removes_lock(sandbox, monkeypatch, evidence):
    _, _, logs, _ = sandbox
    lock = logs / ".git" / "index.lock"
    lock.touch()
    future = time.time() + 2 * 24 * 60 * 60
    monkeypatch.setattr("src.git.git_operations.time.time", lambda: future)
    monkeypatch.setattr(GitOperations, "LOCK_RETRY_DELAY", 0)
    monkeypatch.setattr(
        "src.git.git_operations.shutil.which",
        lambda _: None if evidence == "missing" else "lsof",
    )

    def inspect(*args, **kwargs):
        if evidence == "timeout":
            raise subprocess.TimeoutExpired("lsof", 2)
        if evidence == "changed":
            lock.write_text("replacement")
        return subprocess.CompletedProcess(
            args, 1, "", "inspection denied" if evidence == "error" else ""
        )

    monkeypatch.setattr("src.git.git_operations.subprocess.run", inspect)

    ready = GitOperations(logs).wait_for_locks()

    assert ready is False
    assert lock.exists()


def test_live_lock_released_during_brief_retry(sandbox, monkeypatch):
    _, _, logs, _ = sandbox
    lock = logs / ".git" / "index.lock"
    lock.touch()
    sleeps = []

    def release(delay):
        sleeps.append(delay)
        lock.unlink()

    monkeypatch.setattr("src.git.git_operations.time.sleep", release)

    ready = GitOperations(logs).wait_for_locks()

    assert ready is True
    assert len(sleeps) == 1


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout.strip()


def update(source, message):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "src.update_log",
            source.name,
            str(source),
            git(source, "rev-parse", "HEAD"),
            message,
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )


def test_live_lock_reports_local_save_and_next_run_publishes_backlog(sandbox):
    home, remote, logs, source = sandbox
    lock = logs / ".git" / "index.lock"
    lock.touch()
    before = git(remote, "rev-parse", "main")

    result = update(source, "Blocked entry")

    assert result.returncode == 1
    assert "Saved locally; NOT published" in result.stdout
    assert "stage=lock" in result.stdout
    assert "exit_status=1" in result.stdout
    assert git(remote, "rev-parse", "main") == before
    assert lock.exists()
    pending = list((home / ".captains-log" / "pending").glob("*.json"))
    assert len(pending) == 1
    record = json.loads(pending[0].read_text())
    assert record["stage"] == "lock"
    assert record["sha"] == git(source, "rev-parse", "HEAD")
    assert record["saved_locally"] is True
    for line in result.stdout.splitlines():
        assert all(
            field in line for field in ("timestamp=", "run=", "repo=", "sha=", "stage=")
        )

    lock.unlink()  # Only this test's temporary lock.

    recovered = update(source, "Later entry")

    assert recovered.returncode == 0
    assert "Published" in recovered.stdout
    assert "Blocked entry" in git(remote, "grep", "Blocked entry", "main")
    assert "Later entry" in git(remote, "grep", "Later entry", "main")
    assert git(remote, "rev-list", "--count", f"{before}..main") == "1"
    assert not list((home / ".captains-log" / "pending").glob("*.json"))


def test_retry_publishes_existing_commit_even_with_clean_worktree(sandbox):
    _, remote, logs, source = sandbox
    git(logs, "remote", "set-url", "--push", "origin", str(logs / "missing.git"))

    failed = update(source, "Push failed entry")

    assert failed.returncode == 1
    assert "stage=push" in failed.stdout
    assert not git(logs, "status", "--porcelain")

    git(logs, "remote", "set-url", "--push", "origin", str(remote))

    retried = update(source, "Push failed entry")

    assert retried.returncode == 0
    assert "Push failed entry" in git(remote, "grep", "Push failed entry", "main")


@pytest.mark.parametrize("installer", [cli.setup, cli.install_precommit_hooks])
def test_installed_hook_logs_new_sha_and_never_fails_source_commit(
    sandbox, monkeypatch, installer
):
    home, remote, logs, source = sandbox
    monkeypatch.delenv("GIT_CONFIG_COUNT")
    monkeypatch.delenv("GIT_CONFIG_KEY_0")
    monkeypatch.delenv("GIT_CONFIG_VALUE_0")
    hooks = home / ".git-hooks"
    hooks.mkdir()
    (hooks / "commit-msg").write_text("#!/bin/sh\n# Legacy logger to replace\nexit 0\n")
    installer()
    old_sha = git(source, "rev-parse", "HEAD")
    (logs / ".git" / "index.lock").touch()

    git(source, "commit", "--allow-empty", "-m", "New source commit")

    new_sha = git(source, "rev-parse", "HEAD")
    pending_dir = home / ".captains-log" / "pending"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        records = [json.loads(path.read_text()) for path in pending_dir.glob("*.json")]
        if records and records[0].get("stage") == "lock":
            break
        time.sleep(0.05)
    assert records and records[0]["sha"] == new_sha
    contents = "\n".join(path.read_text() for path in logs.rglob("*.md"))
    assert f"({new_sha[:7]}) New source commit" in contents
    assert f"({old_sha[:7]}) New source commit" not in contents
    assert "New source commit" not in git(remote, "log", "-1", "--format=%s")


@pytest.mark.parametrize("command", ["btw", "wtf", "wnext", "stone"])
def test_manual_entry_commands_surface_pending_background_failures(sandbox, command):
    home, _, logs, source = sandbox
    (logs / ".git" / "index.lock").touch()
    failed = update(source, "Pending background entry")
    assert failed.returncode == 1
    assert list((home / ".captains-log" / "pending").glob("*.json"))

    result = subprocess.run(
        [sys.executable, "-m", f"src.{command}", "Manual note"],
        cwd=source,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert "unpublished Captain's Log run(s)" in result.stdout
    assert str(home / ".captains-log" / "pending") in result.stdout


def test_setup_preserves_message_validation_when_upgrading(sandbox, monkeypatch):
    home, _, _, source = sandbox
    hooks = home / ".git-hooks"
    hooks.mkdir()
    validation = hooks / "commit-msg-precommit"
    validation.write_text("#!/bin/sh\nexit 42\n")
    validation.chmod(0o755)
    for key in ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0"):
        monkeypatch.delenv(key)
    cli.setup()
    before = git(source, "rev-parse", "HEAD")

    result = subprocess.run(
        ["git", "-C", str(source), "commit", "--allow-empty", "-m", "Rejected"],
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode != 0
    assert git(source, "rev-parse", "HEAD") == before
    assert not list((home / ".captains-log" / "pending").glob("*.json"))


@pytest.mark.parametrize("kind", ["first", "amend"])
def test_post_commit_publishes_first_and_amended_commit_sha(sandbox, monkeypatch, kind):
    home, remote, _, source = sandbox
    if kind == "first":
        git(source, "checkout", "--orphan", "fresh")
    for key in ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0"):
        monkeypatch.delenv(key)
    cli.setup()
    arguments = ["--amend"] if kind == "amend" else []

    git(source, "commit", *arguments, "--allow-empty", "-m", f"{kind} source commit")

    sha = git(source, "rev-parse", "HEAD")
    diagnostic = home / ".captains-log" / "update-log.log"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if diagnostic.exists() and "Published log for source" in diagnostic.read_text():
            break
        time.sleep(0.05)
    assert f"({sha[:7]}) {kind} source commit" in git(
        remote, "grep", f"{kind} source commit", "main"
    )
    assert not list((home / ".captains-log" / "pending").glob("*.json"))

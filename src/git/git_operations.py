"""Git operations for Captain's Log."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import time
from pathlib import Path

# Git points these at the invoking repository (and, from a worktree, at its
# private worktree gitdir/index) via the environment for the whole duration
# of a hook. `git -C <other_repo>` only changes the directory used to search
# for a repo and does not override an already-set GIT_DIR/GIT_INDEX_FILE, so
# without stripping these, git commands "targeting" the log repo actually
# operate on whichever repo/worktree triggered the hook.
_GIT_ENV_VARS_TO_STRIP = (
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
)


class GitOperations:
    """Handles git operations for the log repository."""

    # How many times to pull-and-retry a rejected push before giving up.
    MAX_PUSH_RETRIES = 3
    LOCK_RETRIES = 5
    LOCK_RETRY_DELAY = 0.2
    STALE_LOCK_SECONDS = 24 * 60 * 60

    # Git attribute that makes concurrent same-section appends to the log's
    # markdown files merge cleanly (keep every unique line from both sides)
    # instead of producing conflict markers, since entries are always
    # appended and never edited in place.
    MERGE_UNION_ATTRIBUTE = "*.md merge=union"

    def __init__(self, repo_path: Path):
        """Initialize with repository path.

        Args:
            repo_path: Path to the git repository
        """
        self.repo_path = repo_path
        self.stage = "lock"
        self.status_failed = False

    def _git_directories(self):
        """Resolve ordinary and linked-worktree metadata without inherited env."""
        git_dir = self.repo_path / ".git"
        if git_dir.is_file():
            value = git_dir.read_text(encoding="utf-8").strip()
            if not value.startswith("gitdir: "):
                raise ValueError(f"Unrecognized Git directory: {git_dir}")
            git_dir = (self.repo_path / value[8:]).resolve()
        directories = [git_dir]
        common = git_dir / "commondir"
        if common.is_file():
            directories.append((git_dir / common.read_text().strip()).resolve())
        return directories

    def _lock_files(self):
        return [
            path
            for directory in self._git_directories()
            for path in directory.glob("*.lock")
        ]

    def _recover_abandoned_lock(self, path):
        """Fail closed unless an old, unchanged regular lock has no open owner.

        lsof works on macOS and Linux. Missing tools, unsupported platforms,
        inspection errors, symlinks, and changing files all require manual action.
        """
        try:
            before = path.lstat()
            if (
                not stat.S_ISREG(before.st_mode)
                or time.time() - max(before.st_mtime, before.st_ctime)
                < self.STALE_LOCK_SECONDS
            ):
                return False
            lsof = shutil.which("lsof") if os.name == "posix" else None
            if lsof is None:
                return False
            result = subprocess.run(
                [lsof, "-t", str(path.resolve())],
                capture_output=True,
                text=True,
                timeout=2,
            )
            # lsof's documented no-match result: status 1, no output or errors.
            if result.returncode != 1 or result.stdout.strip() or result.stderr.strip():
                return False
            if path.lstat() != before:
                return False
            path.unlink()
            print(
                f"Recovered abandoned Git lock: {path}; publishing pending local entries"
            )
            return True
        except FileNotFoundError:
            return True  # The owning Git process removed it while we waited.
        except (OSError, subprocess.TimeoutExpired):
            return False

    def wait_for_locks(self):
        """Briefly wait for active Git operations, then recover only proven stale locks."""
        self.stage = "lock"
        for attempt in range(self.LOCK_RETRIES + 1):
            locks = self._lock_files()
            if not locks:
                return True
            if attempt < self.LOCK_RETRIES:
                time.sleep(self.LOCK_RETRY_DELAY)
        for path in locks:
            self._recover_abandoned_lock(path)
        remaining = self._lock_files()
        if remaining:
            print(f"Warning: Git locks remain; publication blocked: {remaining}")
            return False
        return True

    def _run_git(self, args: list, **kwargs) -> subprocess.CompletedProcess:
        """Run a git command scoped to repo_path, immune to inherited repo env vars.

        Args:
            args: Arguments to pass after "git" (e.g. ["-C", path, "status"])
            **kwargs: Additional keyword arguments for subprocess.run

        Returns:
            The completed process
        """
        env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_VARS_TO_STRIP}
        return subprocess.run(["git"] + args, env=env, **kwargs)

    def has_changes(self) -> bool:
        """Check if there are any uncommitted changes in the repository.

        Returns:
            True if there are changes, False otherwise
        """
        self.status_failed = False
        try:
            result = self._run_git(
                ["-C", str(self.repo_path), "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            self.status_failed = True
            return False

    def has_lock_files(self) -> bool:
        """Check if there are any git lock files present.

        Returns:
            True if lock files exist, False otherwise
        """
        return bool(self._lock_files())

    def add_file(self, file_path: Path) -> bool:
        """Add a file to the git staging area.

        Args:
            file_path: Path to the file to add

        Returns:
            True if successful, False otherwise
        """
        try:
            relative_path = file_path.relative_to(self.repo_path)
            self._run_git(
                ["-C", str(self.repo_path), "add", str(relative_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except (subprocess.CalledProcessError, ValueError):
            return False

    def _should_publish_path(self, relative_path: str) -> bool:
        """True when a repo-relative path is a .md file or dir containing .md files."""
        if relative_path.endswith(".md"):
            return True
        path_obj = self.repo_path / relative_path
        return path_obj.is_dir() and any(
            f.suffix == ".md" for f in path_obj.rglob("*.md")
        )

    def _add_parent_directories(self, relative_path: str, paths: set[str]) -> None:
        path_obj = self.repo_path / relative_path
        parent = path_obj.parent
        while parent != self.repo_path:
            paths.add(str(parent.relative_to(self.repo_path)))
            next_parent = parent.parent
            if next_parent == parent:
                break
            parent = next_parent

    @staticmethod
    def _parse_porcelain_z(data: bytes) -> list[tuple[str, str, str | None]]:
        """Parse `git status --porcelain -z` into (xy, path, old_path) tuples.

        For renames/copies, path is the destination and old_path is the source.
        """
        entries: list[tuple[str, str, str | None]] = []
        pos = 0
        length = len(data)

        def read_path() -> str:
            nonlocal pos
            end = data.index(0, pos)
            value = data[pos:end].decode("utf-8", "surrogateescape")
            pos = end + 1
            return value

        while pos + 3 <= length:
            status_x, status_y, separator = data[pos], data[pos + 1], data[pos + 2]
            if separator != ord(" "):
                break
            xy = chr(status_x) + chr(status_y)
            pos += 3
            if xy[0] in "RC":
                new_path = read_path()
                old_path = read_path()
                entries.append((xy, new_path, old_path))
            else:
                entries.append((xy, read_path(), None))
        return entries

    def _stage_add_path(self, relative_path: str) -> bool:
        full_path = self.repo_path / relative_path
        if not full_path.exists():
            return True
        try:
            self._run_git(
                ["-C", str(self.repo_path), "add", "--", relative_path],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError as error:
            print(f"Error: git add failed for {relative_path}: {error.stderr or error}")
            return False

    def _stage_deletion(self, relative_path: str) -> bool:
        commands = (
            ["add", "-u", "--", relative_path],
            ["rm", "--cached", "--ignore-unmatch", "--", relative_path],
        )
        last_error = ""
        for command in commands:
            try:
                self._run_git(
                    ["-C", str(self.repo_path), *command],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return True
            except subprocess.CalledProcessError as error:
                last_error = error.stderr or str(error)
        print(f"Error: could not stage deletion for {relative_path}: {last_error}")
        return False

    def add_all(self) -> bool:
        """Stage log-repository changes for commit.

        Reads NUL-separated porcelain status so renames and spaced paths are
        unambiguous. Only .md files and directories that contain .md files are
        staged. Missing rename sources are never passed to ``git add``; deletions
        use ``git add -u``. One failing path is reported but does not abort the
        rest.
        """
        try:
            status_result = self._run_git(
                ["-C", str(self.repo_path), "status", "--porcelain", "-z"],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            return False

        if not status_result.stdout:
            return True

        paths_to_add: set[str] = set()
        paths_to_delete: set[str] = set()

        for xy, path, old_path in self._parse_porcelain_z(status_result.stdout):
            if old_path is not None:
                new_path = path
                if self._should_publish_path(new_path):
                    paths_to_add.add(new_path)
                    self._add_parent_directories(new_path, paths_to_add)
                if self._should_publish_path(old_path):
                    old_full = self.repo_path / old_path
                    if old_full.exists():
                        paths_to_add.add(old_path)
                    elif xy[0] != "R":
                        paths_to_delete.add(old_path)
                continue

            if "D" in xy and self._should_publish_path(path):
                if not (self.repo_path / path).exists():
                    paths_to_delete.add(path)
                continue

            if self._should_publish_path(path):
                paths_to_add.add(path)
                if path.endswith(".md"):
                    self._add_parent_directories(path, paths_to_add)

        failed = False
        for relative_path in sorted(paths_to_add):
            if not self._stage_add_path(relative_path):
                failed = True
        for relative_path in sorted(paths_to_delete):
            if not self._stage_deletion(relative_path):
                failed = True
        return not failed

    def commit(self, message: str) -> bool:
        """Create a commit with the given message.

        Args:
            message: Commit message

        Returns:
            True if successful, False otherwise
        """
        try:
            self._run_git(
                ["-C", str(self.repo_path), "commit", "-m", message],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def push(self) -> bool:
        """Push commits to the remote repository.

        Returns:
            True if successful, False otherwise
        """
        try:
            self._run_git(
                ["-C", str(self.repo_path), "push"],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def pull(self) -> bool:
        """Pull changes from the remote, merging into the current branch.

        Uses a plain merge (not rebase): on conflict the working tree is left
        in a normal "unmerged" state that a clean `git merge --abort` can
        always recover from, which matters since this runs unattended from a
        git hook. If a conflict happens anyway, the merge is aborted so we
        never leave conflict markers sitting in a log file.

        Returns:
            True if the pull succeeded (including a no-op pull), False if
            there was nothing to pull from (no remote/offline) or a conflict
            had to be aborted.
        """
        try:
            self._run_git(
                ["-C", str(self.repo_path), "pull", "--no-rebase"],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            output = f"{e.stdout or ''}{e.stderr or ''}"
            if "CONFLICT" in output:
                self._run_git(
                    ["-C", str(self.repo_path), "merge", "--abort"],
                    capture_output=True,
                    text=True,
                )
                print(
                    "Warning: Pull produced a merge conflict, aborted the merge. "
                    "Resolve manually by running 'git pull' in the log repository."
                )
            else:
                print(f"Warning: Failed to pull changes: {e.stderr or e}")
            return False

    def ensure_merge_driver(self) -> bool:
        """Ensure the log repo's .gitattributes enables union merging for .md files.

        Committing this once (and letting it propagate to every machine via
        the log repo itself) means concurrent appends to the same day's file
        from two machines merge automatically instead of conflicting.

        Returns:
            True if .gitattributes was created or updated, False if it
            already had the attribute or couldn't be read/written.
        """
        gitattributes_path = self.repo_path / ".gitattributes"
        try:
            existing = (
                gitattributes_path.read_text(encoding="utf-8")
                if gitattributes_path.exists()
                else ""
            )
        except OSError:
            return False

        if self.MERGE_UNION_ATTRIBUTE in existing:
            return False

        new_content = existing
        if new_content and not new_content.endswith("\n"):
            new_content += "\n"
        new_content += self.MERGE_UNION_ATTRIBUTE + "\n"

        try:
            gitattributes_path.write_text(new_content, encoding="utf-8")
        except OSError:
            return False

        self.add_file(gitattributes_path)
        return True

    def commit_and_push(self, commit_message: str) -> bool:
        """Perform the complete commit and push workflow.

        Args:
            commit_message: Commit message

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check for lock files
            if not self.wait_for_locks():
                return False

            self.stage = "add"
            self.ensure_merge_driver()

            # Check if there are any changes to commit
            self.stage = "status"
            has_changes = self.has_changes()
            if self.status_failed:
                print("Warning: Failed to inspect Git status")
                return False
            if has_changes:
                # Include entries left by earlier failed runs in the same commit.
                self.stage = "add"
                if not self.add_all():
                    print("Warning: Failed to add files to git")
                    return False
                self.stage = "commit"
                if not self.commit(commit_message):
                    print("Warning: Failed to commit changes")
                    return False

            # Push, retrying with a pull in between if the remote moved on
            # A clean worktree can still have commits from an earlier failed push.
            self.stage = "push"
            if self.push():
                print("Successfully published log updates")
                return True

            for attempt in range(1, self.MAX_PUSH_RETRIES + 1):
                print(
                    f"Warning: Push rejected, pulling and retrying "
                    f"({attempt}/{self.MAX_PUSH_RETRIES})..."
                )
                self.stage = "pull"
                if self.pull() is False:
                    return False
                self.stage = "push"
                if self.push():
                    print("Successfully published log updates")
                    return True

            print("Warning: Failed to push changes")
            return False

        except Exception as e:
            print(f"Warning: Unexpected error during git operations: {e}")
            return False

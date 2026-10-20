"""Correlated run diagnostics and durable records of unpublished local logs."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src import cli_logging


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def pending_directory():
    return Path.home() / ".captains-log" / "pending"


def warn_unpublished():
    """Surface background failures even when this command uses another log repo."""
    records = list(pending_directory().glob("*.json"))
    if records:
        cli_logging.warning(
            f"Warning: {len(records)} unpublished Captain's Log run(s). "
            f"Inspect {pending_directory()} and ~/.captains-log/update-log.log"
        )


class PublicationRun:
    """One run's diagnostic context and pending-state lifecycle.

    Each run has its own marker. Successful publication clears only the snapshot
    of older saved runs for this destination; a concurrent new run stays pending.
    """

    def __init__(self, repo, sha):
        self.run_id = uuid4().hex
        self.repo = repo
        self.sha = sha
        self.stage = "config"
        self.git_ops = None
        self.exit_status = "running"
        self.stream = sys.stdout
        self.buffer = ""
        self.marker = pending_directory() / f"{self.run_id}.json"
        self.record = {}
        self.older = []

    @property
    def current_stage(self):
        return self.git_ops.stage if self.git_ops is not None else self.stage

    def write(self, value):
        """Prefix every diagnostic line, including multiline Git errors."""
        self.buffer += value
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line:
                self.stream.write(
                    f"timestamp={timestamp()} run={self.run_id} "
                    f"repo={json.dumps(self.repo)} sha={json.dumps(self.sha)} "
                    f"stage={self.current_stage} exit_status={self.exit_status} {line}\n"
                )
        self.stream.flush()
        return len(value)

    def flush(self):
        if self.buffer:
            self.write("\n")
        self.stream.flush()

    def isatty(self):
        return False

    def start_pending(self, log_repo, log_file):
        destination = str(log_repo.resolve()) if log_repo else None
        for path in pending_directory().glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if (
                    isinstance(data, dict)
                    and data.get("log_repo") == destination
                    and data.get("saved_locally")
                ):
                    self.older.append(path)
            except (OSError, ValueError):
                continue  # Keep malformed records for inspection.
        self.record = {
            "run": self.run_id,
            "repo": self.repo,
            "sha": self.sha,
            "log_repo": destination,
            "log_file": str(log_file) if log_file else None,
            "saved_locally": False,
        }
        self.update_pending()

    def update_pending(self, **values):
        self.record.update(
            values,
            timestamp=timestamp(),
            stage=self.current_stage,
            exit_status=self.exit_status,
        )
        self.marker.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.marker.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.record, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.marker)

    def published(self):
        for path in [*self.older, self.marker]:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                print(f"Published, but could not clear pending record {path}: {exc}")


def publish_manual_entry(git_ops, log_repo, commit_message):
    """Publish a manual entry; on failure keep a pending marker and return False."""
    run = PublicationRun("manual", "manual")
    run.start_pending(log_repo, None)
    if git_ops.commit_and_push(commit_message):
        run.published()
        return True
    run.stage = git_ops.stage
    run.exit_status = 1
    run.update_pending(saved_locally=True)
    cli_logging.error(f"Saved locally; NOT published; pending={run.marker}")
    return False

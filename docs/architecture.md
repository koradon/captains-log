# Architecture Overview

## Status

current

## Purpose

Captain's Log is a Python CLI that aggregates source commits and manual notes into daily
Markdown logs, optionally stored in a shared Git repository. This overview highlights the
commit publication flow and its failure visibility.

## Requirements to run

The package manifest defines Python, PyYAML, and Typer requirements. Git is required for
automatic commit logging and publication. `captains-log setup` installs global hooks with
the setup interpreter. POSIX `lsof` is optional: without it old locks require manual recovery.

## Execution flow

`post-commit` captures the completed source commit's SHA and subject, then starts
`python -m src.update_log` in the background. `commit-msg` dispatches existing message
validation only. Both setup paths install this split.

The updater loads config, rejects privacy/recursion skips, resolves the project and log
location, and registers pending state. It waits for Git locks and attempts pull before
reading the log. It saves the source entry locally even when synchronization is blocked,
then stages all pending Markdown, commits, and pushes with the existing pull/retry policy.
Old locks are removed only with age, ownership, and unchanged-file evidence. A clean
worktree still attempts push for previously committed but unpublished entries.

Only successful publication clears the applicable saved-run markers. Failed runs return
nonzero and retain stage details. `btw`, `wtf`, `wnext`, and `stone` warn about those markers
before their normal manual-entry flow. This does not add serialization across writers.

## Subsystems / modules

| Module | Responsibility |
| --- | --- |
| `src/app.py`, `src/shortcuts.py` | Unified and standalone CLI entry points |
| `src/cli.py`, `src/hooks/` | Hook rendering, installation, and static templates |
| `src/config/`, `src/projects/` | Configuration, privacy, and source-project resolution |
| `src/entries/`, `src/logs/` | Markdown formatting, deduplication, storage, rollover |
| `src/git/` | Isolated Git subprocess environment, lock handling, commit and sync |
| `src/update_log.py`, `src/publication.py` | Automatic-run orchestration, diagnostics, pending state |

## Data model / storage

Daily Markdown lives in the configured project/global log destination or under
`~/.captains-log/projects/`; yearly milestones use `milestone.md`. Background diagnostics
append to `~/.captains-log/update-log.log`. Atomic per-run JSON records under
`~/.captains-log/pending/` store source repo/SHA, destination, stage, timestamp, save state,
and updater exit status. They are local operational state and are never staged in the log repo.

## Modes / entry points

`captains-log` and the standalone `btw`, `wtf`, `wnext`, `stone` commands share the domain
modules. Automatic logging invokes `src.update_log` directly. Package updates require the
user to rerun setup to migrate existing installed hooks.

## Design principles

Source commits cannot be rejected by log publication. A local save is reported separately
from a push. Unknown lock ownership leaves the lock untouched. Existing Git environment
scrubbing, union merge attributes, and multi-machine synchronization remain in place.

## Related

- [Publication specification](specs/20261020-publication-reliability.md)
- [ADR 0008](adr/0008-observable-post-commit-publication.md)
- [Git environment isolation](adr/0002-scrub-git-env-vars-in-run-git.md)
- [Shared Git synchronization](adr/0003-shared-git-repo-log-storage-with-sync.md)

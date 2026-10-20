# Visible publication outcomes and correct source commits

## Status

accepted

## Summary

An abandoned Git index lock stopped publishing daily logs while local saves continued.
Background logging must distinguish those outcomes and retain inspectable pending state.

## User stories

- As a user, I want a failed publication to remain visible until my entries reach the remote.
- As a user, I want each entry's SHA to identify the commit that supplied its message.

## Requirements

- `update_log` prefixes every processing diagnostic line with UTC `timestamp`, unique `run`,
  source `repo`, full source `sha`, current `stage`, and `exit_status`. The final line records
  the numeric process exit status: 0 for publication or intentional privacy/recursion skips,
  1 for failure, 2 for invalid arguments. A local save in a log directory that is not a Git
  repository is a complete save: exit 0 with no pending record.
- A local save prints `Saved locally`. A failed publication prints `Saved locally; NOT
  published`; only successful push prints `Published`. Config/read/save failures exit 1.
- Before saving to a Git log repository, create `~/.captains-log/pending/<run>.json` atomically, containing the source
  identity, destination, file, timestamp, stage, exit status, and whether the file was saved.
  A failure updates this record. A successful automatic run clears its own record and the
  snapshot of earlier saved records for the same destination. Other destinations,
  incomplete saves, malformed records, and runs started after that snapshot remain visible.
- `btw`, `wtf`, `wnext`, and `stone` report a failed publication of their own entry as
  `Saved locally; NOT published`, exit 1, and leave a pending record; a successful publication
  clears saved records for that destination. They also warn about pending automatic runs, including when a
  duplicate manual entry would cause no write. These warnings are visible at compact level.
- Wait five times for 0.2 seconds for top-level Git locks. Resolve `.git` pointers and common
  directories for linked worktrees. Recover only regular lock files whose mtime **and**
  ctime are at least 24 hours old, after `lsof` on POSIX reports no holder (exit 1, empty
  stdout and stderr), and an immediate second stat matches the original. Never remove
  symlinks or files changed during inspection. Missing tools, unsupported platforms,
  permission errors, and inspection timeouts leave the lock and produce a failure.
- After recovery, keep the existing `add_all()` behavior so all pending local Markdown
  files publish together. Retry push even if the worktree is clean: an earlier run may
  already have committed its entry without publishing it.
- Capture source SHA and subject synchronously in `post-commit`, after the commit exists,
  then launch `update_log` in the background with output appended to
  `~/.captains-log/update-log.log`. Publication failures never veto or delay a user commit.
  Existing pre-commit message validation retains its existing veto behavior.

## Behavior and migration

After upgrading the installed package, the user runs `captains-log setup`. It replaces the
old `~/.git-hooks/commit-msg` logger with a validation dispatcher and installs the new
`post-commit` publisher using the setup interpreter. An existing `commit-msg-precommit`
wrapper is preserved. `captains-log install-precommit-hooks` installs the same dispatcher
and publisher with its wrapper set. Repeated setup is safe and preserves the config.
Package upgrades alone do not rewrite installed hooks.

The shipped `src/hooks/commit-msg` and `commit-msg-package` templates are compatibility
dispatchers. Manual installations must also install the corresponding `post-commit` or
`post-commit-package` template. The package variant uses `python3`; setup pins the package's
interpreter for isolated installs.

Inspect pending JSON files and search `update-log.log` by `run` or full source SHA to
correlate failures. Resolve uncertain locks manually only after inspecting ownership;
the next source commit retries the full local backlog. A manual command warns before its
own work; automatic publication owns clearing automatic-run markers. This change does not
serialize concurrent writers or alter the existing multi-machine merge strategy.

## Acceptance scenarios (BDD)

See [publication-reliability.feature](features/20261020-publication-reliability.feature).
Executable regressions are in `tests/test_publication_reliability.py` and use temporary
homes, clones, and local bare remotes; no test reads or modifies installed user state.

## Related

- [Issue 62](https://github.com/koradon/captains-log/issues/62)
- [ADR 0008](../adr/0008-observable-post-commit-publication.md)

## Open Questions

None.

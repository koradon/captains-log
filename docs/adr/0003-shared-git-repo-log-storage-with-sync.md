# Log storage is a shared git repo, synced pull-before-write

## Status

Accepted

## Context and Problem Statement

A project's log files can be written to from more than one machine — either because the user
works across machines with a shared `global_log_repo`, or because a `log_repo` override points
several projects at the same repo. Every write path (`update_log`, `btw`, `wtf`, `wnext`,
`stone`) reads a day's log file, modifies it, and writes it back. Without coordination, two
machines editing the same day's file independently will silently overwrite each other's entries
whenever the log repo lives in git and gets pushed from both sides.

## Decision Drivers

- Entries must not be silently lost when two machines log on the same day.
- The common case (near-simultaneous appends from different machines) should resolve
  automatically, without the user manually resolving a git conflict.
- A genuine, unresolvable conflict must still fail loudly rather than corrupt the log.

## Considered Options

- Treat the log repo as a plain directory; let the user manage git sync themselves.
- Lock the log repo (e.g. a lockfile or remote lock) during writes to serialize access.
- Back logs with an ordinary git repo, pull before every read, retry push against a moving
  remote, and use a merge driver that unions concurrent appends automatically.

## Decision Outcome

Chosen option: "git repo + pull-before-write + retrying push + union merge driver". Every write
command pulls before loading a day's log file (`GitOperations.pull()`), and
`commit_and_push()` retries the push up to `MAX_PUSH_RETRIES` (3) times, re-pulling in between,
if the remote has moved on since the last pull. `ensure_merge_driver()` commits a
`.gitattributes` rule that assigns a union-merge driver to `*.md` files, so when two machines'
independent commits do need to merge, concurrent appends combine rather than conflict. A real
merge conflict (e.g. two machines editing the same line) still aborts `pull()` cleanly instead
of being force-resolved.

### Consequences

- Good, because the common case — two machines each appending new entries to the same day's
  file — merges automatically with no user intervention.
- Good, because push failures from a moved remote are retried automatically instead of losing
  the commit or requiring the user to notice and re-run.
- Bad, because the union merge driver only works correctly for the specific "append-only
  sections" structure of these log files; it would silently misbehave if the log format ever
  needed line-level edits instead of appends.
- Bad, because a real conflict (not resolvable by union merge) still requires manual
  intervention — `pull()` surfaces this as a clean abort rather than resolving it, by design.

### Confirmation

Committing to the same project's log from two machines in quick succession (simulated via two
clones of the log repo) results in both entries present in the merged log, with no manual `git
merge` step required.

## More Information

See [0001-global-commit-msg-hook-via-core-hookspath.md](0001-global-commit-msg-hook-via-core-hookspath.md)
for why the log repo is written to from a global hook in the first place, and
[0002-scrub-git-env-vars-in-run-git.md](0002-scrub-git-env-vars-in-run-git.md) for the related
environment-isolation fix that keeps these git operations targeting the correct repo.

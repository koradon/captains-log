# Observable publication after source commits exist

## Status

accepted

## Context

`commit-msg` runs before Git creates a commit, so reading HEAD there paired a new
message with the previous SHA. Separately, `commit_and_push()` returned false for any
Git lock while its caller unconditionally reported success. The non-blocking hook
hid four days of failed publication. The requested fix keeps source commits independent
of publication and adds visibility without redesigning synchronization.

## Decision

We capture SHA and subject in `post-commit` before launching the publisher in the
background. Setup replaces the legacy `commit-msg` logger with a dispatcher that preserves
existing message validation. Both installers and shipped templates follow this split.
This updates the hook stage of [ADR 0001](0001-global-commit-msg-hook-via-core-hookspath.md);
the global hooks directory and pinned interpreter remain unchanged.

We retain Boolean Git operation results, expose the current failing stage, and make
`update_log` check the result. Every processing diagnostic carries the run identity and
context. Per-run JSON markers outside the log repository survive failed publication and
are surfaced by existing manual entry commands. Separate records avoid one successful run
clearing another destination or a concurrent new run's state.

We briefly retry locks and recover only old, unchanged regular files with a successful
no-holder inspection. Age alone is insufficient. On platforms without usable `lsof`,
recovery remains manual. Existing staging gathers the full pending backlog; a clean
worktree still requires push because the previous run may have failed after committing.

## Consequences

Source commits remain fast and cannot be rejected by publication failures. Their SHA now
matches the message recorded. Publication failures have nonzero updater status and durable
inspection points even though the hook exits 0. Users must rerun setup after upgrading;
package installation alone cannot migrate the old hook. Conservative recovery can retain
a genuinely abandoned lock when ownership cannot be established. No new dependency or
background service is required, and the existing pull/merge/retry strategy is retained.

## Related

- [Specification](../specs/20261020-publication-reliability.md)
- [Shared Git synchronization](0003-shared-git-repo-log-storage-with-sync.md)

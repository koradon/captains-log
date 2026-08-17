# Scrub git env vars before every subprocess call

## Status

Accepted

## Context and Problem Statement

Because the `commit-msg` hook is global (see
[0001-global-commit-msg-hook-via-core-hookspath.md](0001-global-commit-msg-hook-via-core-hookspath.md)),
it can be invoked while the calling
process still has `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, or `GIT_COMMON_DIR` set in its
environment — for example, a hook fired from inside another repo's worktree, or from a tool that
sets these vars to target a specific checkout. `GitOperations` runs its own git commands with
`-C <target repo>`, but git honors those inherited env vars *before* `-C`, so the command can
silently operate on the wrong repository (the caller's, not the log repo's) instead of failing
loudly.

## Considered Options

- Rely on `-C <path>` alone and hope no caller ever has these vars set.
- Validate the resulting repo path after each git call and error out if it's wrong.
- Strip `GIT_DIR`, `GIT_INDEX_FILE`, `GIT_WORK_TREE`, `GIT_COMMON_DIR` from the subprocess
  environment before every git invocation.

## Decision Outcome

Chosen option: "Strip the git env vars before every subprocess call". `_run_git()` in
`src/git/git_operations.py` builds a copy of the process environment with those four variables
removed before running any git subprocess, so `-C` is always the sole source of truth for which
repository a command targets, regardless of what invoked the hook or what environment it
inherited.

### Consequences

- Good, because every `GitOperations` method (pull, commit, push, merge-driver setup) is
  protected in one place, instead of needing per-call defensive checks.
- Good, because this closes a real, previously-shipped bug (misdirected git operations from
  pooled worktree checkouts) rather than a hypothetical one.
- Bad, because any future code path that needs to *intentionally* target a non-default git dir
  (rather than via `-C`) has to route around this scrubbing explicitly.

## More Information

Shipped together with
[0004-project-grouping-tolerates-pooled-worktrees.md](0004-project-grouping-tolerates-pooled-worktrees.md)
in the same fix (PR #53), which addresses the related project-grouping side of the same
pooled-worktree scenario.

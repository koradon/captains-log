# Global commit-msg hook via core.hooksPath

## Status

Accepted

## Context and Problem Statement

Captain's Log's core promise is to aggregate commit messages into daily logs across every
repository on a machine, without the user having to remember to set anything up per repo. Git
only runs hooks that live inside a repo's own `.git/hooks/` (or a repo-local
`core.hooksPath`), so the naive approach — copying a `commit-msg` script into each repo — would
need to be repeated, and re-applied, for every repo the user ever clones.

## Decision Drivers

- Zero per-repo setup: a new repo should start being logged the moment it's cloned.
- Must not depend on the user remembering to run an install step again.
- Should work regardless of which package manager (pipx, uv, source checkout) installed
  Captain's Log.

## Considered Options

- Per-repo `commit-msg` hook, installed manually or via a project template.
- A background daemon watching all git directories on the machine for new commits.
- One hook installed once via git's global `core.hooksPath` config, shared by every repo.

## Decision Outcome

Chosen option: "One hook installed once via global `core.hooksPath`". `setup()` (`src/cli.py`)
writes a rendered `commit-msg` template into a fixed hooks directory and points git's global
`core.hooksPath` config at it, so every `git commit` on the machine — in any repo — invokes it.
The hook shells out to `python -m src.update_log <repo_name> <repo_path> <commit_sha>
<commit_message>` using `sys.executable` captured at setup time, so it keeps working under
pipx/uv's isolated interpreters rather than depending on `python3` being on `PATH`.

### Consequences

- Good, because a repo is logged automatically from the moment it exists — no per-repo
  onboarding step, ever.
- Good, because there is exactly one hook file to reason about, update, and debug.
- Bad, because it takes over the user's global `core.hooksPath`, which conflicts with any other
  tool or repo that wants to manage that setting; `install_precommit_hooks()` and
  `commit-msg-precommit` exist specifically to let per-repo `.pre-commit-config.yaml` still run
  alongside this hook (see the layered wrapper set in `~/.git-hooks`).
- Bad, because `update_log.py` must defend against being invoked from *any* repo, including ones
  that aren't configured, aren't a Captain's Log project, or are the log repo itself —
  `CommitParser.should_skip_commit()` exists for this reason.

### Confirmation

Cloning a fresh repo and committing to it, with no per-repo setup beyond the one-time global
`setup()`, produces an entry in that day's log file grouped under the new repo's name.

## More Information

See [0002-scrub-git-env-vars-in-run-git.md](0002-scrub-git-env-vars-in-run-git.md) for a related
correctness issue this global-hook approach exposed: a hook invoked from inside one repo's
worktree can leak git environment state that misdirects subsequent git operations toward the
wrong repo.

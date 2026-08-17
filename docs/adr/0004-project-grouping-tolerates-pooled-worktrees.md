# Project grouping tolerates pooled worktree checkouts

## Status

Accepted

## Context and Problem Statement

`ProjectFinder` groups a commit under a project by matching the repo's filesystem path against
configured project roots. Tools such as treehouse pool reusable git worktrees under a path like
`~/.treehouse/<repo>-<hash>/<n>/<repo>`, which is nowhere near that repo's configured project
root. Matching on path alone meant the same logical repo could be logged under two different
project groupings depending on whether it was checked out in its usual location or in a pooled
worktree, splitting one project's history across the daily log.

## Considered Options

- Match strictly by configured path; require pooled worktrees to be explicitly configured as
  their own project root.
- Match by directory name alone, wherever the repo is checked out.
- Match by directory name *and* confirm both checkouts agree on their origin remote (when both
  expose one), grouping under the umbrella root if so.

## Decision Outcome

Chosen option: "directory name + origin remote confirmation". `ProjectFinder.find_project()`
still checks configured project roots first, but a repo checked out entirely outside those
roots is now also grouped under an umbrella root if its directory name matches one of that
root's already-nested repos *and* the two checkouts agree on their origin remote whenever both
expose one. A bare directory-name match alone was rejected as too weak — two unrelated repos
can share a directory name — so the remote check is the guard against false grouping.

### Consequences

- Good, because a repo pooled into a worktree by treehouse (or checked out anywhere else
  entirely) still logs under the same project as its "normal" checkout.
- Good, because the origin-remote check prevents an unrelated repo that happens to share a
  directory name from being merged into the wrong project.
- Bad, because a repo with no configured remote (e.g. a fully local repo) can't be verified this
  way and falls back to directory-name matching alone, which is weaker.

## More Information

Shipped together with
[0002-scrub-git-env-vars-in-run-git.md](0002-scrub-git-env-vars-in-run-git.md) in PR #53. Builds
on the earlier nested-repo support in
`ProjectFinder` (PR #39), which handled repos nested under a configured root but did not yet
handle a repo checked out somewhere unrelated entirely.

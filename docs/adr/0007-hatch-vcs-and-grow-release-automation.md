# Release automation: hatch-vcs + grow.py

## Status

Accepted

## Context

Version numbers previously had to be bumped by hand across the codebase and kept in sync with
git tags for releases, which is easy to get wrong or forget as part of a release.

## Decision

Adopt `hatch-vcs` to derive the installed package version from git tags at build time, writing
the resolved version into the generated `src/_version.py` (excluded from ruff/mypy/coverage,
since it's generated, not authored). Pair this with `grow.py`, a script that bumps the version
in `pyproject.toml` and creates the release commit and tag, so a release is a single command
rather than a manual multi-file edit.

## Consequences

- Easier: the installed package always reports the version matching its actual git tag, with no
  hand-maintained version string to drift out of sync.
- Easier: `grow.py` makes cutting a release (bump + tag + commit) a single repeatable step that
  every contributor follows the same way, rather than an ad hoc process.
- Harder: contributors must remember `src/_version.py` is generated and never hand-edit it (it's
  excluded from lint/type-check/coverage specifically as a reminder of this).

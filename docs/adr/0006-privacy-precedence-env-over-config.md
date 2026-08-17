# Privacy precedence: env var overrides config

## Status

Accepted

## Context

A project can be marked private (excluded from logging) two ways: a `private:` flag in
`~/.captains-log/config.yml`, or the `CAPTAINS_LOG_PRIVATE` environment variable. These can
disagree — for example, a shared config file says a project is not private, but a specific
machine or shell session needs to opt it out temporarily without editing the shared config.

## Decision

`ProjectConfig.is_private()` checks `CAPTAINS_LOG_PRIVATE` first and returns that value if set,
falling back to the config file's `private:` flag, and finally to a default of not-private.
Precedence is env var > config > default.

## Consequences

- Easier: a machine-local or session-local privacy override (e.g. temporarily disabling logging
  for a sensitive project) doesn't require editing a config file that may be shared or synced.
- Harder: privacy behavior for a given project now depends on environment state that isn't
  visible by reading the config file alone, so debugging "why isn't this project being logged"
  requires checking both.

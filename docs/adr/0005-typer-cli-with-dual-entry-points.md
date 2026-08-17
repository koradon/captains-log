# Typer CLI with two entry-point layers

## Status

Accepted

## Context and Problem Statement

Captain's Log needs both a single multi-subcommand CLI (`captains-log btw|wtf|wnext|stone|setup`)
and short standalone commands (`btw "..."`, `wtf "..."`, etc.) that work without the
`captains-log` prefix, since the latter are meant to be typed quickly and often. The original CLI
was hand-rolled `argparse`, and keeping both surfaces (one unified app, several standalone
commands) in sync by hand became increasingly manual as subcommands and options grew.

## Considered Options

- Keep hand-rolled `argparse`, with shared parsing helpers between the unified app and the
  standalone scripts.
- Move to Typer for the unified `captains-log` app only, and reimplement the standalone
  shortcuts as thin wrappers that just call into the Typer app's functions.
- Move to Typer for both layers, accepting duplicated argument definitions between
  `src/app.py` and `src/shortcuts.py` in exchange for each staying a simple, independent Typer
  command.

## Decision Outcome

Chosen option: "Typer for both layers, argument definitions duplicated on purpose". `src/app.py`
defines the unified `captains-log` Typer app with subcommands `btw`, `wtf`, `wnext`, `stone`,
`setup`, `install-precommit-hooks`. `src/shortcuts.py` defines separate single-command Typer
apps (`btw_main`, `wtf_main`, `wnext_main`, `stone_main`), each registered as its own console
script in `[project.scripts]`, so `btw "..."` works standalone. The two layers intentionally
duplicate their argument parsing rather than sharing it, so each shortcut stays a fully
independent, self-contained Typer command.

### Consequences

- Good, because Typer's declarative option/argument definitions replaced significantly more
  manual `argparse` boilerplate, and gave consistent `--help` output for free.
- Good, because each standalone shortcut (`btw`, `wtf`, `wnext`, `stone`) remains simple and
  independently testable, with no shared-parsing indirection to trace through.
- Bad, because a command's options must be changed in two places (`src/app.py` and
  `src/shortcuts.py`) to keep the unified app and the standalone script in sync — a
  maintenance cost accepted deliberately, and called out explicitly in `CLAUDE.md` so it isn't
  missed during future changes.

## More Information

None.

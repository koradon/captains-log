# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Captain's Log is a Python CLI that automatically aggregates git commit messages into daily
markdown logs, grouped by repository and project. It installs a global `commit-msg` git hook
(via `core.hooksPath`) so every commit across every repo on the machine gets logged without
per-repo setup. It also ships standalone commands (`btw`, `wtf`, `wnext`, `stone`) for adding
manual entries alongside the git-derived ones.

## Commands

```bash
uv sync --dev                              # install dev dependencies
uv run pytest                              # run tests (config lives in [tool.pytest.ini_options])
uv run pytest tests/test_wnext.py -v       # run a single test file
uv run pytest -k "test_name_pattern" -v    # run tests matching a pattern
uv run pytest --cov=src --cov-report=term-missing -v   # with coverage
uv run ruff check src/ tests/              # lint
uv run ruff format src/ tests/             # format
uv run mypy src/ --ignore-missing-imports  # type-check
make ci                                    # lint + format-check + test (mirrors CI)
```

`just` recipes (`test`, `test-cov`, `test-file`, `test-pattern`, `install`) wrap the same
commands. Pre-commit is configured (`.pre-commit-config.yaml`, ruff + basic hygiene hooks) via
`make install-hooks` / `make run-hooks`.

pytest is configured with `pythonpath = ["src"]` and `--cov=src` always on, so tests import
via `from src.xxx import ...` rather than a package-relative style.

## Architecture

### Two layers of entry points

- `src/app.py` — the unified `captains-log` Typer app, with subcommands `btw`, `wtf`, `wnext`,
  `stone`, `setup`, `install-precommit-hooks`.
- `src/shortcuts.py` — separate single-command Typer apps (`btw_main`, `wtf_main`,
  `wnext_main`, `stone_main`) registered as their own console scripts in
  `[project.scripts]` (pyproject.toml), so `btw "..."` works standalone without the
  `captains-log` prefix. These duplicate the argument parsing in `app.py` intentionally — keep
  both in sync when changing a command's options.
- `src/cli.py` — `setup()` and `install_precommit_hooks()`, the logic behind those two
  subcommands. Not Typer-based itself; called from `app.py`.
- `src/update_log.py` — the script invoked directly by the installed git hook
  (`python -m src.update_log <repo_name> <repo_path> <commit_sha> <commit_message>`), not
  through the Typer CLI. It also re-exports several "legacy" free functions
  (`load_config_legacy`, `find_project`, `save_log`, etc.) purely for backward-compatible test
  imports — new code should use the domain modules directly, not these wrappers.

### Domain modules under `src/`

Each is a small package with a `*_models.py` (dataclasses) and the logic that operates on them:

- `config/` — loads `~/.captains-log/config.yml` into a `Config`/`ProjectConfig` dataclass
  tree. `ProjectConfig.is_private()` checks the `CAPTAINS_LOG_PRIVATE` env var before falling
  back to the config file's `private:` flag (env > config > default).
- `projects/` — `ProjectFinder` maps a repo path to a `ProjectInfo` by matching configured
  project roots (supports nested repos), falling back to the repo directory name when
  unconfigured.
- `git/` — `GitOperations` (pull/commit/push to the log repo — `pull()` aborts cleanly on a
  real merge conflict, `commit_and_push()` retries push up to `MAX_PUSH_RETRIES` times by
  pulling in between if the remote has moved on, and `ensure_merge_driver()` commits a
  `.gitattributes` union-merge rule for `*.md` so concurrent appends from other machines merge
  without conflicts) and `CommitParser` (parses commit entries, decides whether a commit
  should be skipped — e.g. invalid SHA or running from inside the log repo itself).
- `entries/` — `EntryProcessor`/`EntryFormatter` turn a commit or manual note into a formatted
  markdown line, dedupe entries with the same message but different SHA (amended commits), and
  order the "other" section last.
- `logs/` — `LogManager` resolves where a project's log file lives (`log_repo` override, else
  `global_log_repo`, else `~/.captains-log/projects/<project>/`), and rolls files from previous
  months into `<year>/<month>/` subdirectories automatically. `LogParser`/`LogWriter` handle
  the markdown read/write.

Flow for a commit: `update_log.py` → `load_config()` → `CommitParser.should_skip_commit()` →
`ProjectFinder.find_project()` (bail if `project.is_private`) → `LogManager.get_log_file_info()`
→ `GitOperations.pull()` (if the log lives in a git repo) → `load_log()` →
`EntryProcessor.update_commit_entries()` → `LogManager.save_log()` →
`GitOperations.commit_and_push()` if the log lives in a git repo. `wtf.py`, `wnext.py`, and
`stone.py` follow the same pull-before-read, save-then-commit-and-push pattern, since all four
commands share the same log repo across machines.

### Log file format

Daily files (`YYYY.MM.DD.md`) have three sections in this order: `# What I did` (subsections
per repo name, commit entries as `- (sha) message`, manual `btw` entries under `## other`),
`# Whats next` (subsections per project via `wnext -p`, or `## other`), and a flat
`# What Broke or Got Weird` list from `wtf`. `stone` writes to a separate yearly
`milestone.md` instead of the daily file.

### The git hook itself

`commit-msg` (source install) and `commit-msg-package` (packaged install) are templates
rendered/copied by `cli.py`'s `setup()`. The rendered hook always calls
`python -m src.update_log` using `sys.executable` from the environment that ran `setup()` —
not `python3` off `PATH` — since pipx/uv installs put the package in an isolated interpreter.
`install_precommit_hooks()` layers a `pre-commit`/`commit-msg-precommit`/`pre-push` wrapper set
in `~/.git-hooks` so per-repo `.pre-commit-config.yaml` still runs alongside this hook.

### Versioning

`grow.py` bumps the version in `pyproject.toml` and creates the release commit/tag; CI/release
workflows live in `.github/workflows/`. `src/_version.py` is hatch-vcs-generated — don't edit
it, and it's excluded from ruff/mypy/coverage.

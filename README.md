# Captain's Log

Automatically aggregate your git commit messages daily into markdown logs, grouped by repository and project.

---

## Installation

### Recommended: PyPI + CLI tools

Install Captain's Log as an isolated CLI tool and let the package manage its own dependencies:

```bash
# Using pipx (recommended)
pipx install git-captains-log

# Or using uv
uv pip install git-captains-log

# Or with plain pip (uses your current Python environment)
pip install git-captains-log
```

Then run the setup command:

```bash
captains-log setup
```

This will:
- Create `~/.captains-log/` for configuration
- Create `~/.git-hooks/` for global Git hooks
- Install or update the `commit-msg` hook
- Configure `git config --global core.hooksPath ~/.git-hooks`
- Create a default `~/.captains-log/config.yml` if it does not exist

After that you can use `btw`, `wtf`, `wnext`, `stone`, and `captains-log` from anywhere in your shell.

See [INSTALLATION.md](INSTALLATION.md) for more detailed installation and configuration examples.

### From Source (For Development)

If you're developing Captain's Log locally:

```bash
git clone git@github.com:koradon/captains-log.git
cd captains-log

# Install in editable mode (uses pyproject.toml dependencies)
uv pip install -e .

# Configure hooks and config file
captains-log setup
```

### Pre-commit Integration (Optional)
If you use [pre-commit](https://pre-commit.com/) in your repositories and want to keep both your global Captain's Log hooks and per-repo pre-commit hooks working together, you can install global wrapper hooks via the CLI:

```bash
# After `pipx install git-captains-log` and `captains-log setup`
captains-log install-precommit-hooks
```

This will:
- Install global hook wrappers in `~/.git-hooks` that run pre-commit first (when `.pre-commit-config.yaml` exists)
- Then run Captain's Log afterwards
- Configure `git config --global core.hooksPath ~/.git-hooks` (or reuse the existing value if already correct)
- Work seamlessly with repos that do and do not use pre-commit

**Note:** With pre-commit integration, you don't need to run `pre-commit install` in individual repositories. The global hooks will automatically invoke pre-commit when a repo has `.pre-commit-config.yaml`.

### Configuration

Configure your projects and global log repo in `~/.captains-log/config.yml`:

```yaml
global_log_repo: /path/to/global/log-repo

projects:
  work-repos:
    root: /path/to/work/repos/work-repos

  private-tools:
    root: /path/to/private/repos/tools
    log_repo: /path/to/private-tools/log-repo
```

## Development Setup

This project uses UV for dependency management. To set up the development environment:

1. Install UV if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install development dependencies:
```bash
uv sync --dev
```

3. Run tests:
```bash
uv run pytest
```

4. Run tests with coverage:
```bash
uv run pytest --cov=src --cov-report=term-missing -v
```

5. Run linting:
```bash
uv run ruff check src/ tests/
```

## Usage

### Automatic Git Commit Logging
After setup, every git commit you make will update a daily markdown log file inside the configured log repository/directories.

Logs are grouped by repository name under each project, with a date-based file (e.g., 2025-08-11.md).

### CLI Commands

All commands support `--help` for full usage details, `--version` to show the installed version, and `--log-level compact|verbose|debug` for controlling output verbosity.

Commands can be invoked either as standalone shortcuts or as subcommands of `captains-log`:

```bash
# These are equivalent:
btw "Reviewed the API docs"
captains-log btw "Reviewed the API docs"
```

#### `btw` - Log What You Did
The `btw` (By The Way) command adds manual entries to the "What I did" section of your daily log:

```bash
btw "Reviewed the new API documentation"
btw "Had a productive meeting about the architecture"
btw "Fixed a bug that wasn't committed yet"
```

#### `wtf` - Log Issues and Problems
The `wtf` (What The Fault) command logs issues, bugs, and weird behavior in the "What Broke or Got Weird" section:

```bash
wtf "API endpoint started returning 500 errors"
wtf "Database connection timeout after 10 minutes"
wtf "Tests failing intermittently on CI"
```

#### `wnext` - Log What's Next
The `wnext` command adds items to the "Whats next" section of your daily logs:

```bash
# Default: log under the current project subsection
wnext "Plan sprint backlog refinement"

# Log under a specific project subsection
wnext --project my-project "Prepare release checklist"
wnext -p my-project "Prepare release checklist"

# Log under the generic 'other' subsection
wnext --other "Remember to update the team wiki"
wnext -o "Remember to update the team wiki"
```

#### `stone` - Log Milestones
The `stone` command adds entries to a yearly `milestone.md` file for the current project:

```bash
stone "Shipped v1.0 of the product"
stone "First 1000 users milestone reached"
stone "Completed migration to new infrastructure"
```

#### How They Work:
- **Smart Project Detection**: Uses the same project detection logic as git commits
  - If you're in a configured project directory → logs to that project
  - If not configured → uses the current directory name as project
- **Different Sections**:
  - `btw` entries appear in the "What I did" section under "## other"
  - `wtf` entries appear in the "What Broke or Got Weird" section
  - `wnext` entries appear in the "Whats next" section, grouped by project subsection or under "## other"
  - `stone` entries appear in a separate yearly `milestone.md` file
- **Same Infrastructure**: Uses your existing Captain's Log configuration and repositories

#### Examples:

```bash
# From within your configured project directory
cd ~/work/my-project
btw "Completed code review for new feature"
# → Adds to my-project's daily log under "What I did" → "## other"

wtf "Found memory leak in background worker"
# → Adds to my-project's daily log under "What Broke or Got Weird"

stone "Shipped the background worker rewrite"
# → Adds to my-project's milestone.md

# From any directory
cd ~/Downloads
btw "Downloaded and reviewed the client requirements"
# → Adds to Downloads project log under "What I did"
```

#### Log Format:
Your daily logs will show git commits by repository in "What I did", followed by "Whats next" (with optional subsections) and a flat list in "What Broke or Got Weird":

```markdown
# What I did

## repository-name
- (abc1234) Actual git commit message

## other-repo
- (def5678) Another git commit

## other
- Manual entry added with btw command
- Another manual note

# Whats next

## my-project
- Next action logged with wnext

## other
- General next step logged with wnext --other

# What Broke or Got Weird

- Issue logged with wtf command
- Another problem to investigate
```

## Testing
Run the test suite:

```bash
uv run pytest tests/ -v
```

## Troubleshooting

### Hook not running
- Make sure you've run `captains-log setup` and it completed successfully
- Check that `git config --global core.hooksPath` points to `~/.git-hooks`
- Verify the `commit-msg` file exists in `~/.git-hooks/` and is executable

### Pre-commit integration issues
- Ensure you ran `captains-log setup` before `captains-log install-precommit-hooks`
- Check that both `commit-msg` and `commit-msg-precommit` exist in `~/.git-hooks/`
- If pre-commit errors occur, verify you have pre-commit installed: `pip install pre-commit`
- The integration only runs pre-commit in repos with `.pre-commit-config.yaml`

### Permission errors
- Make sure the hook files are executable
- Check that your user has write access to the log directories

### Conflicting with existing pre-commit setup
If you previously used `pre-commit install` in repositories:
- You can safely leave existing `.git/hooks/` as they won't be used (global `core.hooksPath` takes precedence)
- Or clean them up with `pre-commit uninstall` in each repo if you prefer

### `btw`, `wtf`, `wnext`, or `stone` command not found
If commands are not accessible after installation:
- Verify the package is installed: `pip show git-captains-log` or `pipx list`
- If installed with pipx, ensure `~/.local/bin` is in your PATH
- Reinstall if needed: `pipx install git-captains-log`

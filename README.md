# Captain's Log

Automatically aggregate your git commit messages daily into markdown logs, grouped by repository and project.

---

## Installation

### From PyPI (Recommended for Users)

Install Captain's Log from PyPI:

```bash
# Using pip
pip install git-captains-log

# Or using uv (recommended)
uv pip install git-captains-log
```

Then run the setup command:

```bash
captains-log setup
```

This will configure Git hooks, create config files, and set everything up.

See [INSTALLATION.md](INSTALLATION.md) for detailed installation instructions.

### From Source (For Development)

Use the automated installation script:

```bash
git clone git@github.com:koradon/captains-log.git
cd to/cloned/repo
chmod +x install.sh
./install.sh
```

The `install.sh` script will:
- Create necessary directories (`~/.captains-log` and `~/.git-hooks`)
- Copy `update_log.py` and `commit-msg` hook to the right locations
- Install the `btw` and `wtf` commands globally (accessible from anywhere)
- Set proper executable permissions
- Create a default `config.yml` file
- Configure global git hooks path
- Check for Python 3 and install PyYAML if needed

### Pre-commit Integration (Optional)
If you use [pre-commit](https://pre-commit.com/) in your repositories and want to keep both your global Captain's Log hooks and per-repo pre-commit hooks working together:

```bash
# After running install.sh
chmod +x install-with-precommit.sh
./install-with-precommit.sh
```

This will:
- Install global hook wrappers that run pre-commit first (when `.pre-commit-config.yaml` exists)
- Then run Captain's Log afterwards
- Preserve your existing `core.hooksPath` configuration
- Work seamlessly with repos that don't use pre-commit

**Note:** With pre-commit integration, you don't need to run `pre-commit install` in individual repositories. The global hooks will automatically invoke pre-commit when a repo has `.pre-commit-config.yaml`.

### Manual Installation
If you prefer to install manually:

1. Clone or download Captain's Log:

```bash
git clone git@github.com:koradon/captains-log.git ~/.captains-log
cd ~/.captains-log
```

2. Install dependencies

```bash
pip install pyyaml
```

3. Configure your projects and global log repo in `~/.captains-log/config.yml`

```yaml
global_log_repo: /path/to/global/log-repo

projects:
  work-repos:
    root: /path/to/work/repos/work-repos

  private-tools:
    root: /path/to/private/repos/tools
    log_repo: /path/to/private-tools/log-repo
```

4. Setup Git hooks globally:

```bash
mkdir -p ~/.git-hooks
cp ~/.captains-log/commit-msg ~/.git-hooks/
chmod +x ~/.git-hooks/commit-msg
git config --global core.hooksPath ~/.git-hooks
```

5. Make the Python script executable:

```bash
chmod +x ~/.captains-log/update_log.py
```

## Development Setup

This project uses UV for dependency management and Just for command running. To set up the development environment:

1. Install UV if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install Just if you haven't already:
```bash
# macOS
brew install just

# Linux
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash

# Or with cargo
cargo install just
```

3. Install development dependencies:
```bash
just install-test
```

4. Run tests:
```bash
just test
```

5. Run tests with coverage:
```bash
just test-cov
```

6. Clean up generated files:
```bash
just clean
```

7. Run specific tests:
```bash
just test-file test_update_log.py
just test-pattern "load_config"
```

## Usage

### Automatic Git Commit Logging
After setup, every git commit you make will update a daily markdown log file inside the configured log repository/directories.

Logs are grouped by repository name under each project, with a date-based file (e.g., 2025-08-11.md).

### Manual Log Entries with `btw` and `wtf` Commands

#### `btw` Command - Log What You Did
The `btw` (By The Way) command allows you to add manual entries to your daily logs from anywhere on your system:

```bash
btw "Reviewed the new API documentation"
btw "Had a productive meeting about the architecture"
btw "Fixed a bug that wasn't committed yet"
```

#### `wtf` Command - Log Issues and Problems
The `wtf` (What The Fault) command allows you to log issues, bugs, and weird behavior in the "What Broke or Got Weird" section:

```bash
wtf "API endpoint started returning 500 errors"
wtf "Database connection timeout after 10 minutes"
wtf "Tests failing intermittently on CI"
```

#### How They Work:
- **Smart Project Detection**: Uses the same project detection logic as git commits
  - If you're in a configured project directory → logs to that project
  - If not configured → uses the current directory name as project
- **Different Sections**:
  - `btw` entries appear in the "What I did" section under "## other"
  - `wtf` entries appear in the "What Broke or Got Weird" section
- **Same Infrastructure**: Uses your existing Captain's Log configuration and repositories

#### Examples:

```bash
# From within your configured project directory
cd ~/work/my-project
btw "Completed code review for new feature"
# → Adds to my-project's daily log under "What I did" → "## other"

wtf "Found memory leak in background worker"
# → Adds to my-project's daily log under "What Broke or Got Weird" → "## other"

# From any directory
cd ~/Downloads
btw "Downloaded and reviewed the client requirements"
# → Adds to Downloads project log under "What I did"
```

#### Installation:
Both commands are automatically installed with the main Captain's Log installation:
- Accessible globally from any directory
- Installed to `~/.local/bin/btw` and `~/.local/bin/wtf` (ensure `~/.local/bin` is in your PATH)
- No additional setup required after running `install.sh`

#### Log Format:
Your daily logs will show git commits by repository in "What I did", followed by a flat list in "What Broke or Got Weird":

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


# What Broke or Got Weird

- Issue logged with wtf command
- Another problem to investigate
```

## Testing
To test if your installation is working correctly:

### Basic Captain's Log Test
```bash
python3 test_hook.py
```

This will simulate a commit and show you if the log update is working properly.

### Pre-commit Integration Test
If you installed pre-commit integration, test the dispatcher:

```bash
python3 test_hook_precommit.py
```

This will test that the hook dispatcher correctly runs pre-commit (if configured) followed by Captain's Log.

## Troubleshooting

### Hook not running
- Make sure you've run `install.sh` and it completed successfully
- Check that `git config --global core.hooksPath` points to `~/.git-hooks`
- Verify the `commit-msg` file exists in `~/.git-hooks/` and is executable

### Pre-commit integration issues
- Ensure you ran `install.sh` before `install-with-precommit.sh`
- Check that both `commit-msg` and `commit-msg-precommit` exist in `~/.git-hooks/`
- If pre-commit errors occur, verify you have pre-commit installed: `pip install pre-commit`
- The integration only runs pre-commit in repos with `.pre-commit-config.yaml`

### Script not found errors
- Ensure `update_log.py` was copied to `~/.captains-log/`
- Check that the script has execute permissions: `chmod +x ~/.captains-log/update_log.py`

### Permission errors
- Make sure both the hook and script are executable
- Check that your user has write access to the log directories

### Conflicting with existing pre-commit setup
If you previously used `pre-commit install` in repositories:
- You can safely leave existing `.git/hooks/` as they won't be used (global `core.hooksPath` takes precedence)
- Or clean them up with `pre-commit uninstall` in each repo if you prefer

### `btw` or `wtf` command not found
If the `btw` or `wtf` commands are not accessible:
- Ensure `~/.local/bin` is in your PATH: `echo $PATH | grep ~/.local/bin`
- Add to your shell profile if missing: `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc`
- Verify the symlinks exist: `ls -la ~/.local/bin/btw ~/.local/bin/wtf`
- Re-run the installation if needed: `./install.sh`

# Captain's Log Installation Guide

## For New Users (PyPI Installation)

### Step 1: Install from PyPI

```bash
# Using pip
pip install captainslog

# Or using uv (recommended)
uv pip install captainslog
```

This will install:
- The `btw` command - for adding manual log entries
- The `wtf` command - for logging issues and bugs
- The `captains-log` command - for setup and configuration

### Step 2: Run Setup

```bash
captains-log setup
```

This will:
- Create `~/.captains-log/` directory
- Create `~/.git-hooks/` directory
- Install the Git commit-msg hook
- Configure Git to use the global hooks directory
- Create a default config file at `~/.captains-log/config.yml`

### Step 3: Configure Your Projects

Edit `~/.captains-log/config.yml`:

```yaml
# Where your daily logs will be stored
global_log_repo: /path/to/your/log-repo

# Define your projects
projects:
  my-project:
    root: /path/to/your/repos/my-project

  another-project:
    root: /path/to/repos/another-project
    # Optional: use a different log repo for this project
    log_repo: /path/to/specific/log-repo
```

### Step 4: Start Using It!

```bash
# Make commits as usual - they'll be logged automatically
git commit -m "Added new feature"

# Add manual notes
btw "Reviewed the API documentation"

# Log issues
wtf "API endpoint returning 500 errors"

# Check version
captains-log --version
btw --version
wtf --version
```

## For Developers (Local Installation)

If you're developing Captain's Log:

```bash
# Clone the repository
git clone https://github.com/yourusername/captains-log.git
cd captains-log

# Install in editable mode with uv
uv pip install -e .

# Or run the legacy install script
./install.sh
```

## How It Works

### Installation Flow

```
1. pip install captainslog
   └─> Installs Python package to site-packages
       └─> Creates console scripts:
           ├─> btw (accessible from anywhere)
           ├─> wtf (accessible from anywhere)
           └─> captains-log (accessible from anywhere)

2. captains-log setup
   └─> Creates ~/.captains-log/
       └─> Installs commit-msg hook to ~/.git-hooks/
           └─> Configures Git: core.hooksPath = ~/.git-hooks/
               └─> Creates config.yml

3. User commits in any repository
   └─> Git runs ~/.git-hooks/commit-msg
       └─> Hook calls update_log.py
           └─> Logs commit to daily markdown file
```

### Version Management

Captain's Log uses dynamic versioning based on Git tags:

```bash
# Check current version
captains-log --version

# Versions are derived from Git tags:
# v0.1.0          → Package version: 0.1.0
# v0.1.0 + 3 commits → Package version: 0.1.1.dev3+g1234567
```

## Upgrading

```bash
# Upgrade to the latest version
pip install --upgrade captainslog

# Or with uv
uv pip install --upgrade captainslog

# Run setup again if hooks need updating
captains-log setup
```

## Uninstalling

```bash
# Remove the package
pip uninstall captainslog

# Optionally, remove configuration and hooks
rm -rf ~/.captains-log
rm -rf ~/.git-hooks

# Reset Git hooks path (if you want to remove it)
git config --global --unset core.hooksPath
```

## Troubleshooting

### Commands not found after installation

Make sure `pip` installed scripts are in your PATH:

```bash
# Add to ~/.zshrc or ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

# Then reload your shell
source ~/.zshrc  # or source ~/.bashrc
```

### Hooks not running

```bash
# Check Git hooks path
git config --global core.hooksPath

# Should show: /Users/yourusername/.git-hooks

# Run setup again to reconfigure
captains-log setup
```

### Version shows as 0.0.0.dev0+unknown

This happens when:
- Package is not properly installed
- Running from source without Git repository
- Git tags are missing

Solution:
```bash
# Reinstall the package
pip install --force-reinstall captainslog
```

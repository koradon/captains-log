# Captain’s Log

Automatically aggregate your git commit messages daily into markdown logs, grouped by repository and project.

---

## Installation

1. Clone or download Captain’s Log:

```bash
git clone https://your.git.server/CaptainsLog.git ~/.captains-log
```

2. Install dependencies

```bash
pip install pyyaml
```

3. Configure your projects and global log repo in `~/.captains-log/config.yml`

```yaml
global_log_repo: /path/to/global/log-repo

projects:
  lulu:
    root: /path/to/work/repos/lulu

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

## Usage
After setup, every git commit you make will update a daily markdown log file inside the configured log repository/directories.

Logs are grouped by repository name under each project, with a date-based file (e.g., 2025-08-11.md).

## Testing
To test if your installation is working correctly, run:

```bash
python3 test_hook.py
```

This will simulate a commit and show you if the log update is working properly.

## Troubleshooting

### Hook not running
- Make sure you've run `install.sh` and it completed successfully
- Check that `git config --global core.hooksPath` points to `~/.git-hooks`
- Verify the `commit-msg` file exists in `~/.git-hooks/` and is executable

### Script not found errors
- Ensure `update_log.py` was copied to `~/.captains-log/`
- Check that the script has execute permissions: `chmod +x ~/.captains-log/update_log.py`

### Permission errors
- Make sure both the hook and script are executable
- Check that your user has write access to the log directories

### Python dependencies
- Install PyYAML: `pip install pyyaml`
- Ensure Python 3 is available as `python3`
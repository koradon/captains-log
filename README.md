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
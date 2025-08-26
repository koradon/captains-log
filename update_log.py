#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from datetime import date
import yaml
import subprocess

BASE_DIR = Path.home() / ".captains-log" / "projects"
CONFIG_FILE = Path.home() / ".captains-log" / "config.yml"

HEADER = "# What I did\n\n"
FOOTER = "# Whats next\n\n\n# What Broke or Got Weird\n"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def find_project(repo_path, config):
    projects = config.get("projects", {})
    repo_path_abs = Path(repo_path).resolve()

    # Check configured projects first
    for project_name, proj_cfg in projects.items():
        root_dir = proj_cfg.get("root") if isinstance(proj_cfg, dict) else proj_cfg
        if root_dir is None:
            continue
        root_abs = Path(root_dir).resolve()
        if root_abs in repo_path_abs.parents or root_abs == repo_path_abs:
            return project_name
    
    # fallback: use repository name as project
    return repo_path_abs.name

def load_log(file_path):
    if not file_path.exists():
        return {}
    
    try:
        content = file_path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, IOError) as e:
        print(f"Warning: Could not read log file {file_path}: {e}")
        return {}
    
    repos = {}
    current_repo = None
    for line in content:
        line = line.strip()
        if line.startswith("## "):
            current_repo = line[3:].strip()
            if current_repo:  # Only add non-empty repo names
                repos[current_repo] = []
        elif current_repo and line.startswith("- ") and line.strip():
            repos[current_repo].append(line.strip())
    return repos

def parse_commit_entry(entry):
    if entry.startswith("- (") and ") " in entry:
        sha_end = entry.find(")")
        sha = entry[3:sha_end]
        message = entry[sha_end+2:]
        return sha, message
    return None, None

def update_commit_entries(entries, new_sha, new_msg):
    to_remove = []
    for i, entry in enumerate(entries):
        sha, msg = parse_commit_entry(entry)
        if msg == new_msg and sha != new_sha:
            to_remove.append(i)
        if sha == new_sha and msg == new_msg:
            return entries

    for i in reversed(to_remove):
        entries.pop(i)
    entries.append(f"- ({new_sha}) {new_msg}")
    return entries

def save_log(file_path, repos):
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if not file_path.exists():
            with file_path.open("w", encoding="utf-8") as f:
                f.write(HEADER)
                f.write("\n\n")
                f.write(FOOTER)

        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, IOError):
            # If we can't read the file, start fresh
            content = HEADER + "\n\n" + FOOTER

        if "# What I did" not in content:
            content = HEADER + "\n\n" + FOOTER
        parts = content.split(FOOTER, 1)
        main_part = parts[0].strip()
        footer_part = FOOTER

        commit_lines = []
        for repo in sorted(repos.keys(), key=str.lower):
            commit_lines.append(f"## {repo}")
            commit_lines.extend(repos[repo])
            commit_lines.append("")

        new_content = HEADER + "\n".join(commit_lines).strip() + "\n\n" + footer_part
        
        # Write with atomic operation to avoid corruption
        temp_file = file_path.with_suffix(file_path.suffix + '.tmp')
        temp_file.write_text(new_content, encoding="utf-8")
        temp_file.replace(file_path)
        
    except Exception as e:
        print(f"Error saving log file {file_path}: {e}")
        raise

def commit_and_push(log_repo_path, file_path, commit_msg):
    try:
        # Note: Removed git context guard to allow automatic commit/push from hooks
            
        # Check if there are any git lock files
        git_dir = log_repo_path / ".git"
        lock_files = list(git_dir.glob("*.lock"))
        if lock_files:
            print(f"Warning: Git lock files found, skipping operations: {lock_files}")
            return
            
        # Check if there are any changes to commit
        status_result = subprocess.run(
            ["git", "-C", str(log_repo_path), "status", "--porcelain"], 
            capture_output=True, text=True, check=True
        )
        
        if not status_result.stdout.strip():
            print("No changes to commit, skipping git operations")
            return
            
        # Add the file
        subprocess.run(["git", "-C", str(log_repo_path), "add", str(file_path.relative_to(log_repo_path))], 
                      check=True, capture_output=True, text=True)
        
        # Commit
        subprocess.run(["git", "-C", str(log_repo_path), "commit", "-m", commit_msg], 
                      check=True, capture_output=True, text=True)
        
        # Push
        subprocess.run(["git", "-C", str(log_repo_path), "push"], 
                      check=True, capture_output=True, text=True)
                      
        print(f"Successfully committed and pushed log updates")
        
    except subprocess.CalledProcessError as e:
        print(f"Warning: Git commit/push failed: {e}")
        # Don't retry or loop - just log the error and continue
    except Exception as e:
        print(f"Warning: Unexpected error during git operations: {e}")

def get_log_repo_and_path(project, config):
    global_repo = config.get("global_log_repo")
    project_cfg = config.get("projects", {}).get(project, {})
    if isinstance(project_cfg, dict):
        log_repo = project_cfg.get("log_repo")
        root_dir = project_cfg.get("root")
    else:
        log_repo = None
        root_dir = project_cfg

    if log_repo is None:
        log_repo = global_repo

    today = date.today()
    log_file_name = f"{today.year}.{today.month:02d}.{today.day:02d}.md"

    if log_repo is None:
        log_repo_path = BASE_DIR / project
        log_file = log_repo_path / log_file_name
        return None, log_file

    log_repo_path = Path(log_repo).resolve()
    if log_repo == global_repo:
        log_file = log_repo_path / project / log_file_name
    else:
        log_file = log_repo_path / log_file_name
    return log_repo_path, log_file

def main():
    if len(sys.argv) < 5:
        print("Usage: update_log.py <repo_name> <repo_path> <commit_sha> <commit_message>")
        sys.exit(1)

    repo_name = sys.argv[1]
    repo_path = sys.argv[2]
    commit_sha = sys.argv[3]
    commit_msg = sys.argv[4]

    # Skip if this is a merge commit or if commit_sha is "no-sha"
    if commit_sha == "no-sha" or not commit_sha or commit_sha.startswith("no-sha"):
        print("Skipping log update: No valid commit SHA")
        return

    # Skip if we're in the log repository itself to prevent infinite loops
    config = load_config()
    global_repo = config.get("global_log_repo")
    if global_repo:
        global_repo_abs = Path(global_repo).resolve()
        repo_path_abs = Path(repo_path).resolve()
        # Only skip if we're committing from within the actual log repository
        # This allows commits from captains-log repo to be logged
        if repo_path_abs == global_repo_abs:
            print("Skipping log update: Running from within log repository")
            return

    try:
        config = load_config()
        project = find_project(repo_path, config)

        log_repo_path, log_file = get_log_repo_and_path(project, config)

        repos = load_log(log_file)
        if repo_name not in repos:
            repos[repo_name] = []

        repos[repo_name] = update_commit_entries(repos[repo_name], commit_sha, commit_msg)
        save_log(log_file, repos)

        if log_repo_path is not None:
            commit_and_push(log_repo_path, log_file, f"Update {project} logs for {date.today().isoformat()}")
        
        print(f"Updated log for {repo_name} in project {project}")
    except Exception as e:
        print(f"Error updating log: {e}")
        # Don't exit with error code to avoid breaking git operations
        sys.exit(0)

if __name__ == "__main__":
    main()

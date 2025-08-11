#!/usr/bin/env python3
import sys
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

    for project_name, proj_cfg in projects.items():
        root_dir = proj_cfg.get("root") if isinstance(proj_cfg, dict) else proj_cfg
        if root_dir is None:
            continue
        root_abs = Path(root_dir).resolve()
        if root_abs in repo_path_abs.parents or root_abs == repo_path_abs:
            return project_name
    # fallback: use parent folder name as project
    return repo_path_abs.parent.name

def load_log(file_path):
    if not file_path.exists():
        return {}
    content = file_path.read_text(encoding="utf-8").splitlines()
    repos = {}
    current_repo = None
    for line in content:
        if line.startswith("## "):
            current_repo = line[3:].strip()
            repos[current_repo] = []
        elif current_repo and line.startswith("- "):
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
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if not file_path.exists():
        with file_path.open("w", encoding="utf-8") as f:
            f.write(HEADER)
            f.write("\n\n")
            f.write(FOOTER)

    content = file_path.read_text(encoding="utf-8")
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
    file_path.write_text(new_content, encoding="utf-8")

def commit_and_push(log_repo_path, file_path, commit_msg):
    try:
        subprocess.run(["git", "-C", str(log_repo_path), "add", str(file_path.relative_to(log_repo_path))], check=True)
        subprocess.run(["git", "-C", str(log_repo_path), "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "-C", str(log_repo_path), "push"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Git commit/push failed: {e}")

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

    if log_repo is None:
        log_repo_path = BASE_DIR / project
        log_file = log_repo_path / f"{date.today().isoformat()}.md"
        return None, log_file

    log_repo_path = Path(log_repo).resolve()
    if log_repo == global_repo:
        log_file = log_repo_path / project / f"{date.today().isoformat()}.md"
    else:
        log_file = log_repo_path / f"{date.today().isoformat()}.md"
    return log_repo_path, log_file

def main():
    if len(sys.argv) < 5:
        print("Usage: update_log.py <repo_name> <repo_path> <commit_sha> <commit_message>")
        sys.exit(1)

    repo_name = sys.argv[1]
    repo_path = sys.argv[2]
    commit_sha = sys.argv[3]
    commit_msg = sys.argv[4]

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

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Version bumping script that creates tags and changelog commits."""

import re
import subprocess
import sys
from pathlib import Path

try:
    import tomli
except ImportError:
    try:
        import tomllib as tomli  # Python 3.11+
    except ImportError:
        print("Error: tomli is required. Install with: uv pip install tomli")
        sys.exit(1)


def get_current_version() -> str:
    """Read current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)

    with open(pyproject_path, "rb") as f:
        data = tomli.load(f)

    version = data.get("project", {}).get("version")
    if not version:
        print("Error: version not found in pyproject.toml")
        sys.exit(1)

    return version


def update_version(new_version: str) -> None:
    """Update version in pyproject.toml under [project] section only."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding="utf-8")

    # More reliable: find [project] section and replace version within it
    lines = content.split("\n")
    in_project_section = False
    updated = False

    for i, line in enumerate(lines):
        # Check if we're entering the [project] section
        if line.strip() == "[project]":
            in_project_section = True
            continue

        # Check if we're leaving the [project] section (next top-level section)
        if (
            in_project_section
            and line.strip().startswith("[")
            and not line.strip().startswith("[project.")
        ):
            in_project_section = False
            continue

        # If we're in [project] section, look for version line
        if in_project_section and re.match(r'^\s*version\s*=\s*"', line):
            # Replace the version value
            lines[i] = re.sub(
                r'(version\s*=\s*")[^"]+(")', rf"\g<1>{new_version}\g<2>", line
            )
            updated = True
            break

    if not updated:
        print("Error: Could not find version under [project] section in pyproject.toml")
        sys.exit(1)

    new_content = "\n".join(lines)
    pyproject_path.write_text(new_content, encoding="utf-8")
    print(f"✓ Updated version in pyproject.toml to {new_version}")


def get_last_tag() -> str | None:
    """Get the latest semantic version tag (vX.Y.Z) by version, not history."""

    try:
        # List all tags that look like semantic versions, e.g. v0.1.0
        result = subprocess.run(
            ["git", "tag", "--list", "v[0-9]*.[0-9]*.[0-9]*"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None

    tags = [t.strip() for t in result.stdout.split("\n") if t.strip()]
    if not tags:
        return None

    def parse_tag(tag: str) -> tuple[int, int, int]:
        m = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", tag)
        if not m:
            # Put non-matching tags at the bottom
            return (-1, -1, -1)
        major, minor, patch = m.groups()
        return int(major), int(minor), int(patch)

    # Pick the highest semantic version
    tags.sort(key=parse_tag)
    return tags[-1]


def get_commits_since_tag(tag: str | None) -> list[str]:
    """Get commit messages since the given tag (or all commits if no tag)."""
    if tag:
        range_spec = f"{tag}..HEAD"
    else:
        range_spec = "HEAD"

    try:
        result = subprocess.run(
            ["git", "log", "--pretty=format:%s", range_spec],
            capture_output=True,
            text=True,
            check=True,
        )
        commits = [
            line.strip() for line in result.stdout.strip().split("\n") if line.strip()
        ]
        return commits
    except subprocess.CalledProcessError as e:
        print(f"Error getting commits: {e}")
        sys.exit(1)


def create_changelog(old_version: str, new_version: str, commits: list[str]) -> str:
    """Create a changelog from commit messages."""
    lines = [f"Release {new_version}\n"]
    lines.append(f"Changes since {old_version}:\n")

    if commits:
        for commit in commits:
            lines.append(f"- {commit}")
    else:
        lines.append("- No commits since last release")

    return "\n".join(lines)


def check_git_status() -> None:
    """Check if there are uncommitted changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    if result.stdout.strip():
        print("Warning: You have uncommitted changes.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(1)


def create_tag_and_commit(new_version: str, changelog: str) -> None:
    """Create a commit with changelog and tag it."""
    tag_name = f"v{new_version}"

    # Check if tag already exists
    result = subprocess.run(
        ["git", "tag", "-l", tag_name],
        capture_output=True,
        text=True,
        check=True,
    )
    if result.stdout.strip():
        print(f"Error: Tag {tag_name} already exists")
        sys.exit(1)

    # Stage pyproject.toml
    subprocess.run(["git", "add", "pyproject.toml"], check=True)

    # Create commit
    commit_message = f"Bump version to {new_version}\n\n{changelog}"
    subprocess.run(
        ["git", "commit", "-m", commit_message],
        check=True,
    )
    print(f"✓ Created commit for version {new_version}")

    # Create tag
    subprocess.run(
        ["git", "tag", "-a", tag_name, "-m", f"Release {new_version}"],
        check=True,
    )
    print(f"✓ Created tag {tag_name}")


def push_to_remote() -> None:
    """Push commits and tags to remote."""
    response = input("Push to remote? (y/N): ")
    if response.lower() != "y":
        print("Skipping push. You can push manually with:")
        print("  git push && git push --tags")
        return

    try:
        subprocess.run(["git", "push"], check=True)
        print("✓ Pushed commits to remote")
        subprocess.run(["git", "push", "--tags"], check=True)
        print("✓ Pushed tags to remote")
    except subprocess.CalledProcessError as e:
        print(f"Error pushing to remote: {e}")
        print("You can push manually with:")
        print("  git push && git push --tags")
        sys.exit(1)


def main() -> None:
    """Main function."""
    # Check git status
    check_git_status()

    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")

    # Get last tag
    last_tag = get_last_tag()
    if last_tag:
        print(f"Last tag: {last_tag}")
    else:
        print("No previous tags found")

    # Get commits since last tag
    commits = get_commits_since_tag(last_tag)
    print(f"\nFound {len(commits)} commit(s) since last tag:")

    if commits:
        for i, commit in enumerate(commits[:10], 1):  # Show first 10
            print(f"  {i}. {commit}")
        if len(commits) > 10:
            print(f"  ... and {len(commits) - 10} more")
    else:
        print("  (no commits)")

    # Prompt for new version
    print()
    new_version = input(f"Enter new version (current: {current_version}): ").strip()

    if not new_version:
        print("Error: Version cannot be empty")
        sys.exit(1)

    # Validate version format (basic check)
    if not re.match(r"^\d+\.\d+\.\d+", new_version):
        response = input(
            f"Warning: '{new_version}' doesn't match standard version format (X.Y.Z). "
            "Continue? (y/N): "
        )
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(1)

    # Create changelog
    old_version = last_tag.lstrip("v") if last_tag else current_version
    changelog = create_changelog(old_version, new_version, commits)

    # Show preview
    print("\n" + "=" * 60)
    print("Changelog preview:")
    print("=" * 60)
    print(changelog)
    print("=" * 60)
    print()

    # Confirm
    response = input("Proceed with version bump? (y/N): ")
    if response.lower() != "y":
        print("Aborted.")
        sys.exit(1)

    # Update version
    update_version(new_version)

    # Create commit and tag
    create_tag_and_commit(new_version, changelog)

    # Push to remote
    print()
    push_to_remote()

    print(f"\n✓ Successfully bumped version to {new_version}")


if __name__ == "__main__":
    main()

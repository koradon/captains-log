#!/usr/bin/env python3
"""
Test script for Captain's Log git hook
This script simulates the arguments that would be passed from the commit-msg hook
"""

import os
import subprocess
import sys
from pathlib import Path


def test_hook():
    """Test the update_log.py script with sample data"""

    # Get the current directory as repo path
    repo_path = Path.cwd()
    repo_name = repo_path.name

    # Test commit data
    commit_sha = "test123456789"
    commit_msg = "Test commit message"

    print("Testing Captain's Log hook with:")
    print(f"  Repo name: {repo_name}")
    print(f"  Repo path: {repo_path}")
    print(f"  Commit SHA: {commit_sha}")
    print(f"  Commit message: {commit_msg}")
    print()

    # Run the update script
    script_path = Path.home() / ".captains-log" / "update_log.py"

    if not script_path.exists():
        print(f"Error: Script not found at {script_path}")
        print("Please run install.sh first")
        return False

    try:
        # Set environment variable to prevent recursion
        env = os.environ.copy()
        env["GIT_HOOK"] = "1"

        result = subprocess.run(
            [
                "python3",
                str(script_path),
                repo_name,
                str(repo_path),
                commit_sha,
                commit_msg,
            ],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )

        print("✅ Script completed successfully!")
        print()
        print("Script output:")
        # Filter out git status messages for cleaner output
        output_lines = result.stdout.strip().split("\n")
        for line in output_lines:
            if (
                not line.startswith("On branch")
                and not line.startswith("Your branch")
                and not line.startswith("Untracked files")
            ):
                print(line)

        if result.stderr:
            print("\nScript warnings/errors:")
            stderr_lines = result.stderr.strip().split("\n")
            for line in stderr_lines:
                if line and not line.startswith("fatal:"):
                    print(line)

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Script failed with exit code {e.returncode}")
        print("Script output:")
        print(e.stdout)
        print("Script errors:")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_hook()
    sys.exit(0 if success else 1)

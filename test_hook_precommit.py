#!/usr/bin/env python3
"""
Test script for Captain's Log + pre-commit dispatcher
This simulates a commit-msg invocation by calling hooks/captains-log
with a temporary commit message file.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def test_dispatcher():
    repo_path = Path.cwd()
    dispatcher = repo_path / "hooks" / "captains-log"
    precommit_wrapper = repo_path / "hooks" / "commit-msg-precommit"
    captains_hook = repo_path / "commit-msg"

    if not dispatcher.exists():
        print(f"Error: dispatcher not found at {dispatcher}")
        return False

    # Prepare a temporary commit message file
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        tmp.write("Test commit from test_hook_precommit.py\n\nBody line\n")
        tmp_path = tmp.name

    try:
        # Make sure scripts are executable for the test environment
        for script in (dispatcher, precommit_wrapper, captains_hook):
            if script.exists():
                os.chmod(script, 0o755)

        print("Testing dispatcher with:")
        print(f"  dispatcher: {dispatcher}")
        print(f"  precommit wrapper present: {precommit_wrapper.exists()}")
        print(f"  captains-log hook present: {captains_hook.exists()}")
        print(f"  commit message file: {tmp_path}")
        print()

        env = os.environ.copy()
        # Do not require pre-commit; wrapper will no-op if not present or config missing
        result = subprocess.run(
            [str(dispatcher), tmp_path],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

        print("Dispatcher exit code:", result.returncode)
        if result.stdout:
            print("\nStdout:\n" + result.stdout)
        if result.stderr:
            print("\nStderr:\n" + result.stderr)

        # Success if dispatcher completed (exit 0)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


if __name__ == "__main__":
    ok = test_dispatcher()
    sys.exit(0 if ok else 1)

#!/bin/bash
set -e

# This installer only sets up pre-commit wrapper hooks globally.
# Run ./install.sh first to install Captain's Log itself.

GIT_HOOKS_DIR="$HOME/.git-hooks"

echo "=== Installing pre-commit wrapper hooks (global) ==="

# Ensure hooks directory exists
mkdir -p "$GIT_HOOKS_DIR"

echo "Installing global hook wrappers to $GIT_HOOKS_DIR..."
install_hook() {
  src_path="$1"
  dst_name="$2"
  if [ -f "$src_path" ]; then
    # Default: copy hook as-is
    cp "$src_path" "$GIT_HOOKS_DIR/$dst_name"
    chmod +x "$GIT_HOOKS_DIR/$dst_name"
  else
    echo "Warning: missing $src_path, skipping."
  fi
}

install_hook "hooks/pre-commit" "pre-commit"
install_hook "hooks/commit-msg-precommit" "commit-msg-precommit"
install_hook "hooks/captains-log" "commit-msg"
install_hook "hooks/pre-push" "pre-push"

# Optionally set global git hooks path if different
CURRENT_HOOKS_PATH=$(git config --global core.hooksPath || echo "")
if [ "$CURRENT_HOOKS_PATH" != "$GIT_HOOKS_DIR" ]; then
  echo "Setting global git hooks path to $GIT_HOOKS_DIR"
  git config --global core.hooksPath "$GIT_HOOKS_DIR"
else
  echo "Global git hooks path already set."
fi

# Gentle check that Captain's Log is installed (but do not modify it here)
if [ ! -f "$HOME/.captains-log/update_log.py" ]; then
  echo "Note: Captain's Log not detected at $HOME/.captains-log/update_log.py"
  echo "      Run ./install.sh first if you want Captain's Log integration."
fi

echo "Done. pre-commit wrappers are installed globally."
echo "- They run pre-commit in repos with .pre-commit-config.yaml"
echo "- The commit-msg wrapper will also run Captain's Log if installed"

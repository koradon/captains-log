#!/bin/bash
set -e

CAPT_LOG_DIR="$HOME/.captains-log"
GIT_HOOKS_DIR="$HOME/.git-hooks"
CONFIG_FILE="$CAPT_LOG_DIR/config.yml"

echo "=== Installing Captain's Log ==="

# Create directories
mkdir -p "$CAPT_LOG_DIR"
mkdir -p "$GIT_HOOKS_DIR"

# Copy script and hook
echo "Copying update_log.py and commit-msg..."
cp update_log.py "$CAPT_LOG_DIR/"

# Copy commit-msg hook to git hooks directory (this is where git will look for it)
cp commit-msg "$GIT_HOOKS_DIR/commit-msg"

# Make executables
chmod +x "$CAPT_LOG_DIR/update_log.py"
chmod +x "$GIT_HOOKS_DIR/commit-msg"

# Create basic config.yml if not exist
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Creating default config.yml in $CONFIG_FILE"
  cat > "$CONFIG_FILE" <<EOL
global_log_repo: /path/to/global/log-repo

projects:
  example-project:
    root: /path/to/your/repos/example-project
EOL
else
  echo "Config file already exists, skipping."
fi

# Set global git hooks path
CURRENT_HOOKS_PATH=$(git config --global core.hooksPath || echo "")
if [ "$CURRENT_HOOKS_PATH" != "$GIT_HOOKS_DIR" ]; then
  echo "Setting global git hooks path to $GIT_HOOKS_DIR"
  git config --global core.hooksPath "$GIT_HOOKS_DIR"
else
  echo "Global git hooks path already set."
fi

# Check for python3 and pyyaml
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 is not installed. Please install Python 3 first."
  exit 1
fi

PYTHON_MODULE="yaml"
if ! python3 -c "import $PYTHON_MODULE" &>/dev/null; then
  echo "PyYAML not found, installing via pip..."
  if command -v pip3 &>/dev/null; then
    pip3 install --user pyyaml
  else
    echo "pip3 not found. Please install pip or PyYAML manually."
    exit 1
  fi
else
  echo "PyYAML is already installed."
fi

echo "Installation complete! You can now commit as usual."
echo "Remember to edit your config file at $CONFIG_FILE with your project paths and log repo."

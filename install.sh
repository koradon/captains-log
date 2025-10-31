#!/bin/bash
set -e

CAPT_LOG_DIR="$HOME/.captains-log"
GIT_HOOKS_DIR="$HOME/.git-hooks"
CONFIG_FILE="$CAPT_LOG_DIR/config.yml"

echo "=== Installing Captain's Log ==="

# Create directories
mkdir -p "$CAPT_LOG_DIR"
mkdir -p "$GIT_HOOKS_DIR"

# Copy the entire src directory structure with domain modules
echo "Copying refactored source code and domain modules..."
cp -r src "$CAPT_LOG_DIR/"
cp commit-msg "$CAPT_LOG_DIR/"

# Copy commit-msg hook to git hooks directory (this is where git will look for it)
cp commit-msg "$GIT_HOOKS_DIR/commit-msg"

# Copy btw and wtf wrapper scripts for global access
echo "Installing btw and wtf commands..."
cp btw "$CAPT_LOG_DIR/"
cp wtf "$CAPT_LOG_DIR/"

# Make executables
chmod +x "$CAPT_LOG_DIR/src/update_log.py"
chmod +x "$CAPT_LOG_DIR/src/btw.py"
chmod +x "$CAPT_LOG_DIR/src/wtf.py"
chmod +x "$CAPT_LOG_DIR/commit-msg"
chmod +x "$GIT_HOOKS_DIR/commit-msg"
chmod +x "$CAPT_LOG_DIR/btw"
chmod +x "$CAPT_LOG_DIR/wtf"

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

# Setup PATH for btw command
LOCAL_BIN_DIR="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN_DIR"

# Create symlinks for btw and wtf commands
if [ ! -L "$LOCAL_BIN_DIR/btw" ]; then
  echo "Creating symlink for btw command in $LOCAL_BIN_DIR..."
  ln -sf "$CAPT_LOG_DIR/btw" "$LOCAL_BIN_DIR/btw"
else
  echo "btw command already linked."
fi

if [ ! -L "$LOCAL_BIN_DIR/wtf" ]; then
  echo "Creating symlink for wtf command in $LOCAL_BIN_DIR..."
  ln -sf "$CAPT_LOG_DIR/wtf" "$LOCAL_BIN_DIR/wtf"
else
  echo "wtf command already linked."
fi

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$LOCAL_BIN_DIR:"* ]]; then
  echo ""
  echo "NOTE: $LOCAL_BIN_DIR is not in your PATH."
  echo "To use the 'btw' command from anywhere, add this line to your shell profile:"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo ""
  echo "For example, add it to ~/.zshrc (zsh) or ~/.bashrc (bash):"
  echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
  echo "  source ~/.zshrc"
  echo ""
fi

echo "Installation complete! You can now commit as usual."
echo "Remember to edit your config file at $CONFIG_FILE with your project paths and log repo."
echo ""
echo "New features:"
echo "  - Use 'btw \"your note\"' to add manual entries to your daily log!"
echo "  - Use 'wtf \"what broke\"' to add entries to the 'What Broke or Got Weird' section!"

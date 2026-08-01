#!/bin/bash
set -e

echo "🚀 Starting gtwyguard installation..."

# 1. Define where to put the code
INSTALL_DIR="$HOME/gtwyguard"

# 2. Clone the repository directly to the user's machine
if [ -d "$INSTALL_DIR" ]; then
    echo "📦 Updating existing gtwyguard installation..."
    cd "$INSTALL_DIR"
    git pull origin main --quiet
else
    echo "📦 Downloading gtwyguard..."
    git clone --quiet https://github.com/maskedconquerorofcoding/gtwyguard.git "$INSTALL_DIR"
fi

# 3. Enter the directory and run your actual installer
cd "$INSTALL_DIR"
chmod +x install.sh
./install.sh

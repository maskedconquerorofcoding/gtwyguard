#!/bin/zsh

# 🛡️ gtwyguard & Finder Quick Action Installer for macOS
# Installs gtwyguard antivirus gatekeeper, sets up boot auto-start (LaunchAgent), and integrates macOS Quick Actions

set -e

BOLD="\033[1m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

echo "${CYAN}${BOLD}========================================================================${RESET}"
echo "${CYAN}${BOLD}   🛡️  gtwyguard & Finder Quick Action Installer for macOS               ${RESET}"
echo "${CYAN}${BOLD}========================================================================${RESET}"

# Step 1: Check Python installation
if ! command -v python3 >/dev/null 2>&1; then
    echo "${RED}Error: python3 is required but not installed. Please install Python 3.8+.${RESET}"
    exit 1
fi

INSTALL_DIR="$HOME/gtwyguard"
BIN_DIR="$HOME/.local/bin"
SERVICES_DIR="$HOME/Library/Services"
GTWY_VAULT="$HOME/.gtwyguard"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$LAUNCH_AGENTS_DIR/com.gtwyguard.daemon.plist"

mkdir -p "$BIN_DIR"
mkdir -p "$SERVICES_DIR"
mkdir -p "$GTWY_VAULT"
mkdir -p "$LAUNCH_AGENTS_DIR"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "${YELLOW}[1/5] Copying gtwyguard files to $INSTALL_DIR ...${RESET}"
if [[ "$SCRIPT_DIR" != "$INSTALL_DIR" ]]; then
    mkdir -p "$INSTALL_DIR"
    cp -R "$SCRIPT_DIR/"* "$INSTALL_DIR/" 2>/dev/null || true
fi

# Copy explanation guide to vault & install directory
if [[ -f "$SCRIPT_DIR/AUTOSTART_EXPLANATION.md" ]]; then
    cp "$SCRIPT_DIR/AUTOSTART_EXPLANATION.md" "$GTWY_VAULT/AUTOSTART_EXPLANATION.md"
    cp "$SCRIPT_DIR/AUTOSTART_EXPLANATION.md" "$INSTALL_DIR/AUTOSTART_EXPLANATION.md"
fi

cd "$INSTALL_DIR"

echo "${YELLOW}[2/5] Setting up Python virtual environment & dependencies ...${RESET}"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip >/dev/null 2>&1 || true
pip install -e . >/dev/null

ln -sf "$INSTALL_DIR/.venv/bin/gtwyguard" "$BIN_DIR/gtwyguard"
echo "${GREEN}✓ gtwyguard CLI installed successfully in $BIN_DIR/gtwyguard${RESET}"

echo "${YELLOW}[3/5] Installing Finder Quick Action Terminal scripts ...${RESET}"
if [[ -d "$SCRIPT_DIR/scripts" ]]; then
    cp "$SCRIPT_DIR/scripts/inspect_file_action.sh" "$BIN_DIR/inspect_file_action.sh" 2>/dev/null || true
    chmod +x "$BIN_DIR/inspect_file_action.sh" 2>/dev/null || true
    echo "${GREEN}✓ Quick Action helper scripts installed in $BIN_DIR${RESET}"
fi

echo "${YELLOW}[4/5] Installing Finder Quick Action Workflows into macOS Services ...${RESET}"
if [[ -d "$SCRIPT_DIR/workflows" ]]; then
    cp -R "$SCRIPT_DIR/workflows/"* "$SERVICES_DIR/" 2>/dev/null || true
    echo "${GREEN}✓ Quick Actions installed in $SERVICES_DIR${RESET}"
fi

echo ""
echo "${YELLOW}[5/5] macOS Boot Auto-Start Configuration ...${RESET}"

# Prompt user with macOS native dialog
RESPONSE=""
if command -v osascript >/dev/null 2>&1; then
    RESPONSE=$(osascript -e '
        try
            set resultButton to button returned of (display dialog "Would you like gtwyguard to start automatically in the background when your Mac boots?" buttons {"Refuse", "Allow Auto-Start"} default button "Allow Auto-Start" with icon caution title "gtwyguard Security Gatekeeper")
            return resultButton
        on error
            return "Refuse"
        end try
    ' 2>/dev/null || echo "Refuse")
else
    RESPONSE="Refuse"
fi

if [[ "$RESPONSE" == "Allow Auto-Start" ]]; then
    echo "${GREEN}✓ User approved boot auto-start.${RESET}"
    
    # Create LaunchAgent plist
    cat << EOF > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gtwyguard.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>$BIN_DIR/gtwyguard</string>
        <string>watch</string>
        <string>--dir</string>
        <string>$HOME/Downloads</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$GTWY_VAULT/daemon.log</string>
    <key>StandardErrorPath</key>
    <string>$GTWY_VAULT/daemon.log</string>
</dict>
</plist>
EOF
    
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH" 2>/dev/null || true
    echo "${GREEN}${BOLD}✓ LaunchAgent configured & loaded! gtwyguard will now auto-start when your Mac boots.${RESET}"
else
    echo "${RED}${BOLD}⚠️  BOOT AUTO-START REFUSED${RESET}"
    echo "${YELLOW}Real-time download monitoring will NOT start automatically when your Mac boots.${RESET}"
    echo "${YELLOW}Without auto-start, downloaded files will NOT be screened before gaining system access.${RESET}"
    echo ""
    echo "${CYAN}${BOLD}📖 Read the explanation file to see why gtwyguard requires auto-start:${RESET}"
    EXPLANATION_PATH="$INSTALL_DIR/AUTOSTART_EXPLANATION.md"
    echo "${BOLD}${CYAN}file://${EXPLANATION_PATH}${RESET}"
    echo ""
    
    # Automatically open explanation file in default viewer (or TextEdit/Preview)
    if [[ -f "$EXPLANATION_PATH" ]]; then
        open "$EXPLANATION_PATH" 2>/dev/null || true
    fi
fi

echo ""
echo "${GREEN}${BOLD}========================================================================${RESET}"
echo "${GREEN}${BOLD}✨ INSTALLATION COMPLETE!                                               ${RESET}"
echo "${GREEN}${BOLD}========================================================================${RESET}"
echo "You can now:"
echo " 1. Right-click any file in Finder -> Quick Actions -> 'Scan for Prompt Injections (gtwyguard)'"
echo " 2. Run 'gtwyguard watch' manually if auto-start was refused."
echo " 3. Check status at any time: 'gtwyguard status'"
echo ""

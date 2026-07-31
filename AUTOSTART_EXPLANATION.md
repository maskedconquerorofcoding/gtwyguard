# ⚠️ Why gtwyguard Auto-Start is Required for Real-Time Protection

## 🛡️ Executive Summary

`gtwyguard` is designed as a **real-time security gatekeeper**. It monitors incoming files (e.g. in `~/Downloads`), intercepts unverified downloads, quarantines suspicious assets, and scans for prompt injections **before** files can interact with your system, AI agents, or local terminal.

---

## 🚫 What Happens When Auto-Start is Disabled?

If auto-start is **refused** or disabled:

1. **No Automatic Protection on Boot**:
   When you restart your Mac, the `gtwyguard` background watcher daemon will **not** be running.

2. **Unscreened Downloads**:
   Any file downloaded from web browsers, email attachments, or external sources will **not be intercepted or screened**. They will land directly in your filesystem without security validation.

3. **Risk of Prompt Injection Execution**:
   Malicious scripts, prompt injections, or exfiltration vectors embedded in downloaded Markdown/Python/Code files can be inadvertently opened or executed by your local AI tools, terminal scripts, or agent workflows before you realize they are dangerous.

4. **Manual Overhead**:
   You will have to manually open a Terminal and type `gtwyguard watch --dir ~/Downloads` every single time you log into your Mac to maintain protection.

---

## ⚙️ How to Enable Auto-Start Later

If you refused auto-start during installation but want to enable it now:

### Option 1: Re-run the Installer
Open Terminal, navigate to your installer directory, and run:
```bash
./install.sh
```
Select **"Allow Auto-Start"** when prompted.

### Option 2: Manually Register the macOS LaunchAgent
Run the following commands in Terminal:

```bash
# 1. Create the LaunchAgents directory if it doesn't exist
mkdir -p ~/Library/LaunchAgents

# 2. Create the service configuration
cat << 'EOF' > ~/Library/LaunchAgents/com.gtwyguard.daemon.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gtwyguard.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/$USER/.local/bin/gtwyguard</string>
        <string>watch</string>
        <string>--dir</string>
        <string>/Users/$USER/Downloads</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/$USER/.gtwyguard/daemon.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/$USER/.gtwyguard/daemon.log</string>
</dict>
</plist>
EOF

# 3. Load the background daemon immediately
launchctl load ~/Library/LaunchAgents/com.gtwyguard.daemon.plist
```

---

## 🔍 Verification

To verify whether the `gtwyguard` background daemon is currently active:

```bash
launchctl list | grep com.gtwyguard.daemon
```
If active, you will see a process ID listed next to `com.gtwyguard.daemon`.

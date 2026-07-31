# 🛡️ gtwyguard

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Non-Commercial](https://img.shields.io/badge/License-PolyForm%20Noncommercial-orange.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)]()

**gtwyguard** is a custom security gatekeeper and file processor that monitors downloaded files and source code, quarantines unverified assets, and scans for prompt injections before allowing access to local system services or terminal execution environments.

---

## ✨ Features

- 🔍 **Prompt Injection Detection**: Static analysis scanner for detecting prompt injections, hidden exfiltration vectors, and unauthorized system commands embedded in files.
- 📦 **Automated Downloads Gatekeeper**: Real-time folder monitoring (e.g. `~/Downloads`) to intercept new files and quarantine them automatically.
- 🔒 **Quarantine Manager**: Safe local staging area (`~/.gtwyguard/quarantine`) with inspection, manual release, and purge actions.
- 🍏 **macOS Finder Integration**: Built-in Quick Action workflows (`Scan for Prompt Injections (gtwyguard)` and `Inspect File`) accessible via right-click in macOS Finder.
- ⚡ **Rich Terminal Interface**: Built with `rich` for clear visual security reports and instant threat evaluation.

---

## 🚀 Quick Start

### Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/YOUR_USERNAME/gtwyguard.git
cd gtwyguard
pip install -e .
```

### Basic Commands

```bash
# Scan a file or directory for prompt injections
gtwyguard scan /path/to/file_or_dir

# Launch background download watcher for ~/Downloads
gtwyguard watch --dir ~/Downloads

# View quarantined files and security status
gtwyguard status

# Release a file from quarantine after verification
gtwyguard release <ID_OR_PATH>

# Permanently delete a quarantined file
gtwyguard purge <ID_OR_PATH>
```

---

## 🍏 macOS Finder Integration

To enable right-click Quick Actions in macOS Finder:

1. Unzip `gtwyguard_antivirus_bundle.zip` or navigate to `dist_package/`.
2. Run the automated installer:
   ```bash
   cd dist_package
   ./install.sh
   ```
3. Right-click any file or folder in Finder → **Quick Actions** → **`Scan for Prompt Injections (gtwyguard)`**.

---

## 🧪 Running Tests

To execute the test suite:

```bash
python -m unittest discover tests
```

---

## 📄 License & Attribution

This project is created by **Jedidiah Roberts** and licensed under the **PolyForm Noncommercial 1.0.0 License with Attribution** (see [LICENSE](LICENSE)).

- **Non-Commercial Use Only**: Free to use, modify, and distribute for non-commercial purposes.
- **Attribution Required**: Must retain full credit to Jedidiah Roberts in all copies and derivatives.
- **Custom Versions & Derivatives**: You may create custom versions and hold copyright over your unique additions if they are substantially different from the original codebase. Commercial sale of the software or direct derivatives is prohibited without explicit permission.

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

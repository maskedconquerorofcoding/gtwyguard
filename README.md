
<img width="601" height="388" alt="Screenshot 2026-08-01 at 12 53 27 pm" src="https://github.com/user-attachments/assets/ab231a30-8bec-4d50-be44-8ee574495cd9" />
<img width="597" height="390" alt="Screenshot 2026-08-01 at 12 21 36 pm" src="https://github.com/user-attachments/assets/1d10cc7a-4095-47ae-8cc3-fe4a2f4003d8" />
<img width="605" height="393" alt="Screenshot 2026-08-01 at 12 21 01 pm" src="https://github.com/user-attachments/assets/60c07385-31f5-4e2f-b10c-caadf4cad584" />
<img width="598" height="390" alt="Screenshot 2026-08-01 at 12 21 21 pm" src="https://github.com/user-attachments/assets/477f1534-781f-499c-9728-b741e7343cb7" />

---

<img width="954" height="682" alt="Screenshot 2026-07-31 at 12 36 07 am" src="https://github.com/user-attachments/assets/c3a8986c-cadc-44ff-9c49-ed93b9515acb" />
<img width="632" height="519" alt="Screenshot 2026-07-31 at 12 36 42 am" src="https://github.com/user-attachments/assets/abbeaad3-4d36-4b92-9ae6-70a21b8dff58" />
<img width="592" height="393" alt="Screenshot 2026-07-31 at 12 37 22 am" src="https://github.com/user-attachments/assets/56b170a9-785c-42ab-9952-67e870660a1a" />
<img width="587" height="391" alt="Screenshot 2026-07-31 at 12 38 24 am" src="https://github.com/user-attachments/assets/c1778e06-bf19-49ef-b599-ac7c778b247d" />

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
## ⬇️🔄 How to Install

Run this command:  `curl -sSL https://raw.githubusercontent.com/maskedconquerorofcoding/gtwyguard/main/bootstrap.sh | bash`

---
## 📄 License & Attribution

This project is created by **Jedidiah Roberts** and licensed under the **PolyForm Noncommercial 1.0.0 License with Attribution** (see [LICENSE](LICENSE)).

- **Non-Commercial Use Only**: Free to use, modify, and distribute for non-commercial purposes.
- **Attribution Required**: Must retain full credit to Jedidiah Roberts in all copies and derivatives.
- **Custom Versions & Derivatives**: You may create custom versions and hold copyright over your unique additions if they are substantially different from the original codebase. Commercial sale of the software or direct derivatives is prohibited without explicit permission.

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

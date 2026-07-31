import os
import sys
import json
import shutil
import stat
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

VAULT_DIR = Path.home() / ".gtwyguard"
QUARANTINE_DIR = VAULT_DIR / "quarantine"
METADATA_FILE = VAULT_DIR / "metadata.json"

class QuarantineManager:
    """Manages file quarantine, metadata tracking, and permission locks/releases."""

    def __init__(self):
        VAULT_DIR.mkdir(parents=True, exist_ok=True)
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        if not METADATA_FILE.exists():
            self._save_metadata({})

    def _load_metadata(self) -> Dict[str, Any]:
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_metadata(self, data: Dict[str, Any]):
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def quarantine_file(self, target_path: str, scan_summary: Dict[str, Any]) -> str:
        """Quarantine a file or folder by locking execution permissions and registering in vault."""
        abs_path = os.path.abspath(target_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Path does not exist: {abs_path}")

        # Set restrictive permissions (no execution permission)
        self._apply_permission_lock(abs_path)

        # Apply macOS xattr quarantine if on Darwin
        if sys.platform == "darwin":
            try:
                subprocess.run(
                    ["xattr", "-w", "com.apple.quarantine", "0081;gtwyguard;PromptInjectionLock;", abs_path],
                    stderr=subprocess.DEVNULL,
                    check=False
                )
            except Exception:
                pass

        file_id = f"q_{hash(abs_path) & 0xffffffff:08x}"
        metadata = self._load_metadata()
        metadata[file_id] = {
            "id": file_id,
            "original_path": abs_path,
            "filename": os.path.basename(abs_path),
            "status": "QUARANTINED",
            "timestamp": datetime.now().isoformat(),
            "scan_summary": scan_summary
        }
        self._save_metadata(metadata)
        return file_id

    def release_file(self, file_id_or_path: str) -> bool:
        """Release a quarantined file, restoring access and permissions."""
        metadata = self._load_metadata()
        target_entry = None
        target_id = None

        abs_input = os.path.abspath(file_id_or_path)
        for fid, entry in metadata.items():
            if fid == file_id_or_path or entry.get("original_path") == abs_input:
                target_entry = entry
                target_id = fid
                break

        if not target_entry:
            # Fallback: release path directly if exists
            if os.path.exists(abs_input):
                self._restore_permissions(abs_input)
                return True
            return False

        path = target_entry["original_path"]
        if os.path.exists(path):
            self._restore_permissions(path)
            if sys.platform == "darwin":
                try:
                    subprocess.run(["xattr", "-d", "com.apple.quarantine", path], stderr=subprocess.DEVNULL, check=False)
                except Exception:
                    pass

        target_entry["status"] = "APPROVED"
        target_entry["released_at"] = datetime.now().isoformat()
        metadata[target_id] = target_entry
        self._save_metadata(metadata)
        return True

    def reject_and_delete(self, file_id_or_path: str) -> bool:
        """Purge a rejected file from system."""
        metadata = self._load_metadata()
        target_entry = None
        target_id = None

        abs_input = os.path.abspath(file_id_or_path)
        for fid, entry in metadata.items():
            if fid == file_id_or_path or entry.get("original_path") == abs_input:
                target_entry = entry
                target_id = fid
                break

        path = target_entry["original_path"] if target_entry else abs_input
        if os.path.exists(path):
            self._restore_permissions(path)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

        if target_id and target_id in metadata:
            metadata[target_id]["status"] = "PURGED"
            self._save_metadata(metadata)
        return True

    def get_quarantined_items(self) -> List[Dict[str, Any]]:
        metadata = self._load_metadata()
        return [entry for entry in metadata.values() if entry.get("status") == "QUARANTINED"]

    def _apply_permission_lock(self, path: str):
        """Remove write and execute permissions to lock file down."""
        try:
            if os.path.isfile(path):
                os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH) # 0444 read-only
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for f in files:
                        fp = os.path.join(root, f)
                        os.chmod(fp, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        except Exception as e:
            print(f"[gtwyguard] Warning: Permission lock on {path}: {e}")

    def _restore_permissions(self, path: str):
        """Restore user read/write/execute permissions."""
        try:
            if os.path.isfile(path):
                # Standard read/write
                os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for d in dirs:
                        os.chmod(os.path.join(root, d), stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)
                    for f in files:
                        fp = os.path.join(root, f)
                        os.chmod(fp, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        except Exception as e:
            print(f"[gtwyguard] Warning: Restore permissions on {path}: {e}")

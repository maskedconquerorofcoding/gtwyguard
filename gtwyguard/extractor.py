import os
import zipfile
import tarfile
import tempfile
from typing import List, Tuple, Optional

TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".sh", ".bash", ".zsh", ".md", ".markdown",
    ".txt", ".json", ".yaml", ".yml", ".html", ".htm", ".css", ".c", ".cpp", ".h",
    ".rs", ".go", ".rb", ".php", ".xml", ".csv", ".ini", ".env", ".toml", ".prompt"
}

class Extractor:
    """Handles unpacking archives and traversing directories to extract scannable text files."""

    @classmethod
    def is_archive(cls, path: str) -> bool:
        lower = path.lower()
        return lower.endswith(".zip") or lower.endswith(".tar") or lower.endswith(".tar.gz") or lower.endswith(".tgz")

    @classmethod
    def is_scannable_file(cls, path: str) -> bool:
        ext = os.path.splitext(path)[1].lower()
        if ext in TEXT_EXTENSIONS or os.path.basename(path).startswith(".env"):
            return True
        # Read first 512 bytes to check if it's text/ascii
        try:
            with open(path, "rb") as f:
                chunk = f.read(512)
                if not chunk:
                    return False
                # Check for null bytes (binary file heuristic)
                return b'\x00' not in chunk
        except Exception:
            return False

    @classmethod
    def get_files_to_scan(cls, target_path: str) -> Tuple[List[str], Optional[tempfile.TemporaryDirectory]]:
        """
        Returns a list of file paths to scan. If target_path is an archive,
        it unpacks it to a temporary directory (returned so caller can clean up).
        """
        abs_path = os.path.abspath(target_path)
        temp_dir = None

        if not os.path.exists(abs_path):
            return [], None

        if os.path.isfile(abs_path):
            if cls.is_archive(abs_path):
                temp_dir = tempfile.TemporaryDirectory(prefix="gtwyguard_extract_")
                extracted_path = temp_dir.name
                if abs_path.lower().endswith(".zip"):
                    with zipfile.ZipFile(abs_path, 'r') as zip_ref:
                        zip_ref.extractall(extracted_path)
                elif abs_path.lower().endswith((".tar", ".tar.gz", ".tgz")):
                    with tarfile.open(abs_path, 'r:*') as tar_ref:
                        tar_ref.extractall(extracted_path)
                return cls._scan_directory(extracted_path), temp_dir
            elif cls.is_scannable_file(abs_path):
                return [abs_path], None
            else:
                return [], None

        elif os.path.isdir(abs_path):
            return cls._scan_directory(abs_path), None

        return [], None

    @classmethod
    def _scan_directory(cls, dir_path: str) -> List[str]:
        scannable = []
        for root, _, files in os.walk(dir_path):
            # Skip hidden git or cache dirs
            if "/." in root or "\\." in root:
                continue
            for f in files:
                fp = os.path.join(root, f)
                if cls.is_scannable_file(fp):
                    scannable.append(fp)
        return scannable

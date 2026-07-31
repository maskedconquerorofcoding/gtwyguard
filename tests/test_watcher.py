import os
import shutil
import tempfile
import unittest
from gtwyguard.quarantine import QuarantineManager
from gtwyguard.watcher import DownloadGuardHandler

class TestDownloadGuardHandler(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="gtwyguard_watch_test_")
        self.qm = QuarantineManager()
        self.handler = DownloadGuardHandler(quarantine_mgr=self.qm, auto_release_safe=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_safe_download_auto_release(self):
        safe_path = os.path.join(self.test_dir, "downloaded_safe.py")
        with open(safe_path, "w") as f:
            f.write("print('Normal script')\n")
        
        self.handler._process_path(safe_path)
        items = self.qm.get_quarantined_items()
        # Safe download should auto-release
        self.assertFalse(any(i["original_path"] == safe_path for i in items))

if __name__ == "__main__":
    unittest.main()

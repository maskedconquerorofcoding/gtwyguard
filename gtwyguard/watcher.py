import os
import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console

from gtwyguard.scanner import PromptScanner, Severity
from gtwyguard.extractor import Extractor
from gtwyguard.quarantine import QuarantineManager
from gtwyguard.report import render_scan_report

console = Console()

class DownloadGuardHandler(FileSystemEventHandler):
    """File system event handler that intercepts downloads, quarantines them, and scans for prompt injections."""

    def __init__(self, quarantine_mgr: QuarantineManager, auto_release_safe: bool = True):
        super().__init__()
        self.quarantine_mgr = quarantine_mgr
        self.scanner = PromptScanner()
        self.auto_release_safe = auto_release_safe
        self.processed_files = set()

    def on_created(self, event):
        if event.is_directory:
            return
        self._process_path(event.src_path)

    def _process_path(self, file_path: str):
        abs_path = os.path.abspath(file_path)

        # Ignore temporary download files (.crdownload, .download, .tmp, metadata files)
        if any(abs_path.endswith(ext) for ext in [".crdownload", ".download", ".tmp", ".part"]):
            return
        if abs_path in self.processed_files or "/.gtwyguard" in abs_path:
            return

        self.processed_files.add(abs_path)

        # Allow time for file write to complete
        time.sleep(0.5)
        if not os.path.exists(abs_path):
            return

        console.print(f"\n[bold cyan]🛡️ gtwyguard Intercepted New Download:[/bold cyan] [white]{abs_path}[/white]")

        # Step 1: Quarantining immediately before access
        files_to_scan, temp_dir = Extractor.get_files_to_scan(abs_path)

        results = []
        for fp in files_to_scan:
            res = self.scanner.scan_file(fp)
            if res.total_injections > 0 or res.error:
                results.append(res)

        total_injections = sum(r.total_injections for r in results)
        
        scan_summary = {
            "total_files_scanned": len(files_to_scan),
            "total_injections": total_injections,
            "results": [
                {
                    "file": r.file_path,
                    "injections": r.total_injections,
                    "severity": r.highest_severity,
                    "findings": [
                        {
                            "line": f.line_number,
                            "pattern": f.pattern_name,
                            "severity": f.severity,
                            "matched": f.matched_text,
                            "description": f.description
                        } for f in r.findings
                    ]
                } for r in results
            ]
        }

        # Step 2: Lock down file in Quarantine
        file_id = self.quarantine_mgr.quarantine_file(abs_path, scan_summary)

        # Step 3: Render detailed report
        render_scan_report(results, os.path.basename(abs_path), file_id=file_id)

        # Step 4: Handle release or user confirmation
        if total_injections == 0 and self.auto_release_safe:
            self.quarantine_mgr.release_file(file_id)
            console.print(f"[bold green]✨ File auto-cleared and released from quarantine.[/bold green] (Safe for terminal/service access)\n")
            self._send_macos_notification("gtwyguard Security Gatekeeper", f"Safe Download Released: {os.path.basename(abs_path)}", "No prompt injections found.")
        else:
            self._send_macos_notification(
                "🚨 gtwyguard Security Alert",
                f"Prompt Injections Found ({total_injections})",
                f"{os.path.basename(abs_path)} quarantined. User review required."
            )
            self._prompt_user_action(file_id, abs_path)

        if temp_dir:
            temp_dir.cleanup()

    def _send_macos_notification(self, title: str, subtitle: str, message: str):
        if sys.platform == "darwin":
            try:
                script = f'display notification "{message}" with title "{title}" subtitle "{subtitle}"'
                subprocess.run(["osascript", "-e", script], stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass

    def _prompt_user_action(self, file_id: str, file_path: str):
        console.print(f"[bold yellow]What action would you like to take on quarantined file?[/bold yellow]")
        console.print(f"  [1] Approve & Release (Grant access to system/terminal)")
        console.print(f"  [2] Keep Quarantined")
        console.print(f"  [3] Delete File")

        try:
            choice = input("Select option [1/2/3]: ").strip()
            if choice == "1":
                self.quarantine_mgr.release_file(file_id)
                console.print(f"[bold green]✅ Approved & Released:[/bold green] {file_path}")
            elif choice == "3":
                self.quarantine_mgr.reject_and_delete(file_id)
                console.print(f"[bold red]🗑️ File Deleted:[/bold red] {file_path}")
            else:
                console.print(f"[bold yellow]🔒 File remains locked in quarantine:[/bold yellow] {file_path}")
        except Exception:
            console.print(f"[bold yellow]🔒 File remains locked in quarantine.[/bold yellow]")

def start_watcher(watch_dir: str = "~/Downloads"):
    target_dir = os.path.expanduser(watch_dir)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    quarantine_mgr = QuarantineManager()
    handler = DownloadGuardHandler(quarantine_mgr=quarantine_mgr)

    observer = Observer()
    observer.schedule(handler, path=target_dir, recursive=False)
    observer.start()

    console.print(f"[bold cyan]🛡️ gtwyguard Daemon Active[/bold cyan]")
    console.print(f"  Watching Directory: [white]{target_dir}[/white]")
    console.print(f"  Quarantine Vault:   [white]{Path.home()}/.gtwyguard[/white]")
    console.print(f"  Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[bold yellow]gtwyguard Daemon Stopped.[/bold yellow]")
    observer.join()

import os
import sys
import argparse
from rich.console import Console
from rich.table import Table

from gtwyguard.scanner import PromptScanner
from gtwyguard.extractor import Extractor
from gtwyguard.quarantine import QuarantineManager
from gtwyguard.report import render_scan_report
from gtwyguard.watcher import start_watcher

console = Console()

def main():
    parser = argparse.ArgumentParser(
        prog="gtwyguard",
        description="🛡️ gtwyguard - Download & Source Code Prompt Injection Gatekeeper"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subcommand: scan
    scan_parser = subparsers.add_parser("scan", help="Scan a file, archive, or folder for prompt injections.")
    scan_parser.add_argument("path", help="Path to file, directory, or archive (.zip, .tar.gz)")
    scan_parser.add_argument("--quarantine", action="store_true", help="Quarantine file if prompt injections are found.")

    # Subcommand: watch
    watch_parser = subparsers.add_parser("watch", help="Start background watcher daemon on a directory (default: ~/Downloads).")
    watch_parser.add_argument("--dir", default="~/Downloads", help="Directory to monitor for new downloads.")

    # Subcommand: status
    status_parser = subparsers.add_parser("status", help="List all currently quarantined files awaiting review.")

    # Subcommand: release
    release_parser = subparsers.add_parser("release", help="Release a quarantined file and restore access.")
    release_parser.add_argument("target", help="Quarantine ID or file path to release.")

    # Subcommand: purge
    purge_parser = subparsers.add_parser("purge", help="Purge/delete a rejected quarantined file.")
    purge_parser.add_argument("target", help="Quarantine ID or file path to purge.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    qm = QuarantineManager()

    if args.command == "scan":
        target = os.path.abspath(args.path)
        if not os.path.exists(target):
            console.print(f"[bold red]Error:[/bold red] Target path does not exist: {target}")
            sys.exit(1)

        console.print(f"[bold cyan]Scanning:[/bold cyan] {target} ...")
        files_to_scan, temp_dir = Extractor.get_files_to_scan(target)

        scanner = PromptScanner()
        results = []
        for fp in files_to_scan:
            res = scanner.scan_file(fp)
            if res.total_injections > 0 or res.error:
                results.append(res)

        file_id = ""
        total_injections = sum(r.total_injections for r in results)
        if args.quarantine and total_injections > 0:
            scan_summary = {"total_files_scanned": len(files_to_scan), "total_injections": total_injections}
            file_id = qm.quarantine_file(target, scan_summary)
            console.print(f"[bold yellow]🔒 File quarantined with ID:[/bold yellow] {file_id}")

        render_scan_report(results, os.path.basename(target), file_id=file_id)

        if temp_dir:
            temp_dir.cleanup()

    elif args.command == "watch":
        start_watcher(watch_dir=args.dir)

    elif args.command == "status":
        items = qm.get_quarantined_items()
        if not items:
            console.print("[bold green]✅ No quarantined items pending review.[/bold green]")
            return

        table = Table(title="🔒 Quarantined Files Pending Review", show_header=True, header_style="bold yellow")
        table.add_column("ID", style="bold cyan", width=12)
        table.add_column("File Name", style="bold white", width=25)
        table.add_column("Original Path", style="dim white")
        table.add_column("Injections", style="bold red", width=12)
        table.add_column("Timestamp", style="dim white", width=20)

        for item in items:
            summary = item.get("scan_summary", {})
            table.add_row(
                item["id"],
                item["filename"],
                item["original_path"],
                str(summary.get("total_injections", 0)),
                item["timestamp"][:19]
            )
        console.print(table)

    elif args.command == "release":
        if qm.release_file(args.target):
            console.print(f"[bold green]✅ Released file from quarantine:[/bold green] {args.target}")
        else:
            console.print(f"[bold red]Failed to release target:[/bold red] {args.target}")

    elif args.command == "purge":
        if qm.reject_and_delete(args.target):
            console.print(f"[bold red]🗑️ Purged file from system:[/bold red] {args.target}")
        else:
            console.print(f"[bold red]Failed to purge target:[/bold red] {args.target}")

if __name__ == "__main__":
    main()

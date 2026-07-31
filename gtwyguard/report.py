from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from typing import List
from gtwyguard.scanner import ScanResult, Severity

console = Console()

SEVERITY_COLORS = {
    Severity.CLEAN: "bold green",
    Severity.LOW: "bold cyan",
    Severity.MEDIUM: "bold yellow",
    Severity.HIGH: "bold magenta",
    Severity.CRITICAL: "bold white on red"
}

SEVERITY_EMOJIS = {
    Severity.CLEAN: "✅",
    Severity.LOW: "ℹ️",
    Severity.MEDIUM: "⚠️",
    Severity.HIGH: "🚨",
    Severity.CRITICAL: "🔥"
}

def render_scan_report(results: List[ScanResult], target_name: str, file_id: str = ""):
    total_files = len(results)
    total_injections = sum(r.total_injections for r in results)
    
    highest_severity = Severity.CLEAN
    for r in results:
        if Severity.priority(r.highest_severity) > Severity.priority(highest_severity):
            highest_severity = r.highest_severity

    sev_color = SEVERITY_COLORS.get(highest_severity, "white")
    emoji = SEVERITY_EMOJIS.get(highest_severity, "🔍")

    # Header Panel
    status_text = Text()
    status_text.append(f"Target Scanned: ", style="bold white")
    status_text.append(f"{target_name}\n", style="bold cyan")
    if file_id:
        status_text.append(f"Quarantine ID: ", style="bold white")
        status_text.append(f"{file_id}\n", style="dim yellow")
    status_text.append(f"Overall Risk Level: ", style="bold white")
    status_text.append(f" {emoji} {highest_severity} ", style=sev_color)
    status_text.append(f"  |  Files Scanned: {total_files}  |  Prompt Injections Found: ", style="bold white")
    status_text.append(f"{total_injections}", style="bold red" if total_injections > 0 else "bold green")

    console.print()
    console.print(Panel(status_text, title="[bold cyan]🛡️ gtwyguard Security Assessment[/bold cyan]", border_style="cyan"))

    if total_injections == 0:
        console.print(Panel("[bold green]✅ No prompt injections or malicious execution directives detected in source files.[/bold green]\nFile is safe to access local services and terminal.", title="[bold green]CLEAN REPORT[/bold green]", border_style="green"))
        return

    # Findings Table
    table = Table(title="🔍 Detected Prompt Injections & Security Risks", show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Line", style="dim white", width=6)
    table.add_column("Pattern & Risk Category", style="bold white", width=28)
    table.add_column("Severity", width=12)
    table.add_column("Matched Content Snippet & Risk Details", style="white")

    for res in results:
        for f in res.findings:
            badge_color = SEVERITY_COLORS.get(f.severity, "white")
            sev_badge = f"[{badge_color}] {SEVERITY_EMOJIS.get(f.severity, '')} {f.severity} [/{badge_color}]"
            
            # Format snippet details
            detail_text = f"[bold yellow]File:[/bold yellow] {res.file_path}\n"
            detail_text += f"[bold red]Matched:[/bold red] '{f.matched_text}'\n"
            detail_text += f"[bold white]Context:[/bold white] {f.line_content}\n"
            detail_text += f"[dim cyan]Risk:[/dim cyan] {f.description}"

            table.add_row(
                str(f.line_number),
                f.pattern_name,
                sev_badge,
                detail_text
            )

    console.print(table)
    console.print()

    # Risk Explanation & Action Box
    risk_summary = Text()
    risk_summary.append("⚠️ WARNING: This file contains prompt injections that could trick AI tools or local agents into executing unauthorized terminal commands or accessing system resources.\n\n", style="bold yellow")
    risk_summary.append("Before releasing this file from quarantine, verify that the code/prompt matches your expectations.", style="dim white")

    console.print(Panel(risk_summary, title="[bold red]🚨 Security Risk Advisory[/bold red]", border_style="red"))

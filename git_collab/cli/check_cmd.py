"""gc check — Proactive conflict detection across branches.

Scans all active branches against a base branch and reports which
branches modify the same Python symbols, warning about potential
merge conflicts BEFORE they happen.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from git_collab.core.git_ops import GitOps
from git_collab.semantic.conflict_detector import detect_conflicts

console = Console(safe_box=True)


def check_cmd(
    base: str = typer.Option("main", "--base", "-b", help="Base branch to compare against."),
    branches: list[str] | None = typer.Option(None, "--branch", "-B", help="Specific branches to check (default: all)."),
) -> None:
    """Scan active branches for potential merge conflicts.

    Analyzes which Python functions and classes are modified in each
    branch, and warns when two branches touch the same symbols.
    """
    git = GitOps()

    if not git.branch_exists(base):
        console.print(f"[red]Error:[/] Base branch '{base}' does not exist.")
        raise typer.Exit(1)

    console.print(f"[cyan]Scanning branches against[/] [bold]{base}[/] ...\n")

    overlaps = detect_conflicts(git, base_branch=base, branches=branches)

    if not overlaps:
        console.print(
            Panel(
                "[green][OK] No overlapping symbol modifications detected![/]\n"
                "All active branches can be merged independently.",
                title="Conflict Check",
                border_style="green",
            )
        )
        return

    # Build the results table
    table = Table(
        title="[!] Cross-Branch Conflict Risk",
        show_header=True,
        header_style="bold",
        safe_box=True,
    )
    table.add_column("Branch A", style="cyan")
    table.add_column("Branch B", style="magenta")
    table.add_column("File", style="dim")
    table.add_column("Overlapping Symbol")
    table.add_column("Risk", justify="center")

    risk_colors = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}

    for overlap in overlaps:
        risk_style = risk_colors.get(overlap.risk, "white")
        table.add_row(
            overlap.branch_a,
            overlap.branch_b,
            overlap.file_path,
            overlap.symbol_name,
            f"[{risk_style}][{overlap.risk}][/{risk_style}]",
        )

    console.print(table)
    console.print()

    # Summary
    high = sum(1 for o in overlaps if o.risk == "HIGH")
    med = sum(1 for o in overlaps if o.risk == "MEDIUM")
    low = sum(1 for o in overlaps if o.risk == "LOW")

    console.print(
        Panel(
            f"[red]HIGH: {high}[/]  [yellow]MEDIUM: {med}[/]  [green]LOW: {low}[/]\n\n"
            f"[bold]HIGH[/] = Same function/class modified in both branches (will conflict)\n"
            f"[bold]MEDIUM[/] = Same file modified (may conflict)\n"
            f"[bold]LOW[/] = Same package modified (unlikely to conflict)",
            title=f"Summary - {len(overlaps)} overlap(s) found",
            border_style="yellow",
        )
    )

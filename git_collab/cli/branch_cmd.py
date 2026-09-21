"""gc branch — Branch health dashboard.

Shows information about all branches: staleness, divergence
from main, last commit, and merge readiness.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from git_collab.core.git_ops import GitOps

console = Console(safe_box=True)


def branch_cmd(
    base: str = typer.Option("main", "--base", "-b", help="Base branch to compare against."),
) -> None:
    """Show branch health dashboard — staleness, divergence, and readiness.

    Displays a table of all local branches with their commit counts
    ahead/behind the base branch, last commit date, and overall health.
    """
    git = GitOps()

    if not git.branch_exists(base):
        console.print(f"[red]Error:[/] Base branch '{base}' does not exist.")
        raise typer.Exit(1)

    branches = git.list_branches()

    if len(branches) <= 1:
        console.print("[dim]Only one branch exists. Nothing to compare.[/]")
        return

    console.print(f"[cyan]Branch health relative to[/] [bold]{base}[/]\n")

    table = Table(show_header=True, header_style="bold", safe_box=True)
    table.add_column("Branch", style="cyan")
    table.add_column("Status", justify="center", width=10)
    table.add_column("Ahead", justify="right", width=7)
    table.add_column("Behind", justify="right", width=7)
    table.add_column("Changed Files", justify="right", width=14)
    table.add_column("Last Commit", width=18)
    table.add_column("Message")

    for branch_name in sorted(branches):
        if branch_name == base:
            continue

        info = git.get_branch_info(branch_name, base)

        # Determine health status
        if info.commits_behind > 20:
            status = "[red][STALE][/]"
        elif info.commits_behind > 5:
            status = "[yellow][BEHIND][/]"
        elif info.commits_ahead == 0:
            status = "[dim][MERGED][/]"
        else:
            status = "[green][OK][/]"

        # Active branch marker
        name_display = f"[bold]> {branch_name}[/]" if info.is_active else branch_name

        table.add_row(
            name_display,
            status,
            str(info.commits_ahead),
            str(info.commits_behind),
            str(len(info.changed_files)),
            info.last_commit_date,
            info.last_commit_message[:50],
        )

    console.print(table)

    # Summary
    total = len(branches) - 1  # exclude base
    console.print(f"\n[dim]{total} branch(es) compared against '{base}'[/]")

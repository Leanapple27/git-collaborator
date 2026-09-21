"""gc resolve — Interactive TUI conflict resolver.

Launches a full-screen terminal UI showing conflicted files
with side-by-side OURS/THEIRS views and one-key resolution actions.
"""

from __future__ import annotations

import ast

import typer
from rich.console import Console
from rich.panel import Panel

from git_collab.core.git_ops import GitOps
from git_collab.core.diff3 import extract_three_way

console = Console()


def resolve_cmd(
    file: str | None = typer.Argument(None, help="Specific conflicted file to resolve."),
) -> None:
    """Interactively resolve merge conflicts with a visual TUI.

    Shows OURS and THEIRS side-by-side, lets you pick a resolution,
    and validates the result is valid Python before saving.
    """
    git = GitOps()

    if not git.is_merge_in_progress():
        console.print("[yellow]No merge in progress.[/] Run 'gc merge <branch>' first.")
        raise typer.Exit(1)

    conflicted = git.get_conflicted_files()
    if not conflicted:
        console.print("[green]No conflicted files found.[/] Merge is clean.")
        return

    # Filter to specific file if provided
    if file:
        if file not in conflicted:
            console.print(f"[red]Error:[/] '{file}' is not in the conflicted files list.")
            console.print(f"Conflicted files: {', '.join(conflicted)}")
            raise typer.Exit(1)
        files_to_resolve = [file]
    else:
        files_to_resolve = conflicted

    console.print(f"[cyan]Found {len(files_to_resolve)} conflicted file(s).[/]\n")

    resolved_count = 0

    for file_path in files_to_resolve:
        console.print(f"[bold]Resolving:[/] {file_path}")

        # Extract 3-way content
        # During an active merge, we need to get the branch being merged
        # from MERGE_HEAD
        try:
            merge_head = (git.repo_root / ".git" / "MERGE_HEAD").read_text().strip()
        except FileNotFoundError:
            console.print("[red]Error:[/] Cannot determine merge source.")
            continue

        three_way = extract_three_way(git, file_path, merge_head)

        if three_way.is_python:
            # Launch TUI for Python files
            try:
                from git_collab.tui.app import ResolverApp

                tui_app = ResolverApp(
                    ours_content=three_way.ours,
                    theirs_content=three_way.theirs,
                    file_path=file_path,
                )
                tui_app.run()

                if tui_app.resolved_content is not None:
                    # Validate Python syntax
                    try:
                        ast.parse(tui_app.resolved_content)
                    except SyntaxError as e:
                        console.print(
                            f"[yellow]Warning:[/] Resolved content has syntax error: {e.msg}"
                        )
                        if not typer.confirm("Save anyway?"):
                            console.print("[dim]Skipped.[/]")
                            continue

                    git.write_and_stage(file_path, tui_app.resolved_content)
                    resolved_count += 1
                    console.print(f"  [green]✓ Resolved and staged.[/]")
                else:
                    console.print(f"  [dim]Skipped (quit without saving).[/]")

            except ImportError:
                console.print("[red]Error:[/] Textual not installed. Run: pip install textual")
                raise typer.Exit(1)
        else:
            # Non-Python files: show simple choice
            console.print(f"  [dim](Non-Python file — simple resolution)[/]")
            choice = typer.prompt(
                "Accept [o]urs, [t]heirs, or [s]kip?",
                default="s",
            )
            if choice.lower() == "o":
                git.write_and_stage(file_path, three_way.ours)
                resolved_count += 1
                console.print(f"  [green]✓ Accepted ours.[/]")
            elif choice.lower() == "t":
                git.write_and_stage(file_path, three_way.theirs)
                resolved_count += 1
                console.print(f"  [green]✓ Accepted theirs.[/]")
            else:
                console.print(f"  [dim]Skipped.[/]")

    # Summary
    console.print()
    remaining = len(files_to_resolve) - resolved_count
    if remaining == 0:
        console.print(
            Panel(
                f"[green]✓ All {resolved_count} file(s) resolved![/]\n"
                f"Run [bold]git commit[/] to finalize the merge.",
                title="Resolution Complete",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                f"Resolved: {resolved_count} | Remaining: {remaining}\n"
                f"Run [bold]gc resolve[/] again to continue.",
                title="Resolution Progress",
                border_style="yellow",
            )
        )

"""gc merge — AST-aware smart merge command.

Merges a branch into the current branch using semantic Python analysis.
Auto-resolves import conflicts and independent function changes.
Falls back to standard merge for non-Python files.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

from git_collab.core.git_ops import GitOps
from git_collab.core.diff3 import extract_three_way_from_refs
from git_collab.semantic.import_merger import merge_imports, format_imports
from git_collab.semantic.function_merger import merge_functions

console = Console(safe_box=True)


def merge_cmd(
    branch: str = typer.Argument(help="Branch to merge into the current branch."),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Preview merge without applying."),
) -> None:
    """Merge a branch using AST-aware conflict resolution.

    Automatically resolves:
    - Import statement conflicts (union + sort + dedup)
    - Independent function/class additions and modifications

    Flags true semantic conflicts for manual resolution.
    """
    git = GitOps()

    if not git.branch_exists(branch):
        console.print(f"[red]Error:[/] Branch '{branch}' does not exist.")
        raise typer.Exit(1)

    current = git.current_branch
    console.print(f"[cyan]Merging[/] [bold]{branch}[/] into [bold]{current}[/] ...")

    # Find merge base
    merge_base_sha = git.merge_base(current, branch)
    if not merge_base_sha:
        console.print("[red]Error:[/] No common ancestor found between branches.")
        raise typer.Exit(1)

    # Get changed Python files
    py_files = git.get_changed_python_files(merge_base_sha, branch)
    our_changed = git.get_changed_python_files(merge_base_sha, current)

    # Find files changed in BOTH branches (potential conflicts)
    conflicting_py_files = set(py_files) & set(our_changed)
    theirs_only_files = set(py_files) - set(our_changed)

    if not py_files and not our_changed:
        console.print("[green]No Python file changes detected.[/] Running standard git merge...")
        success = git.start_merge(branch, no_commit=False)
        if success:
            console.print("[green][OK] Merge completed cleanly.[/]")
        else:
            console.print("[yellow]Standard merge has conflicts. Use 'gc resolve' to fix them.[/]")
        return

    # ── Attempt standard merge first ─────────────────────────────
    # If git merge succeeds with no conflicts, we're done
    if not conflicting_py_files:
        console.print(f"[dim]No overlapping Python files. Running standard merge...[/]")
        success = git.start_merge(branch, no_commit=False)
        if success:
            console.print("[green][OK] Merge completed cleanly (no Python conflicts).[/]")
        else:
            console.print("[yellow]Non-Python conflicts detected. Resolve manually or use 'gc resolve'.[/]")
        return

    console.print(
        f"\n[yellow][!] {len(conflicting_py_files)} Python file(s) changed in both branches.[/]"
    )
    console.print("[cyan]Running AST-aware semantic merge...[/]\n")

    if dry_run:
        console.print("[dim](Dry run — no changes will be applied)[/]\n")

    # ── Semantic merge for each conflicting Python file ───────────
    auto_resolved_files = []
    conflict_files = []

    for file_path in sorted(conflicting_py_files):
        console.print(f"  Analyzing [bold]{file_path}[/] ...")

        # Get 3-way content
        three_way = extract_three_way_from_refs(
            git, file_path, merge_base_sha, current, branch
        )

        # Try import merging
        import_result = merge_imports(three_way.base, three_way.ours, three_way.theirs)

        # Try function/class merging
        func_result = merge_functions(three_way.base, three_way.ours, three_way.theirs)

        if func_result.conflicts:
            conflict_names = [c.name for c in func_result.conflicts]
            console.print(
                f"    [red][X] True conflicts:[/] {', '.join(conflict_names)}"
            )
            conflict_files.append((file_path, func_result))
        else:
            auto_resolved = func_result.auto_resolved
            if import_result.had_conflicts:
                console.print(f"    [yellow][!] Import conflicts need manual review[/]")
                conflict_files.append((file_path, func_result))
            else:
                console.print(
                    f"    [green][OK] Auto-resolved[/] "
                    f"({len(auto_resolved)} symbol(s) merged)"
                )
                auto_resolved_files.append((file_path, func_result.merged_source))

    # ── Apply results ─────────────────────────────────────────────
    console.print()

    if not dry_run and auto_resolved_files:
        # Start the actual merge
        git.start_merge(branch, no_commit=True)

        for file_path, merged_source in auto_resolved_files:
            git.write_and_stage(file_path, merged_source)

        if not conflict_files:
            sha = git.commit(f"Merge branch '{branch}' (AST-resolved by gc)")
            console.print(
                Panel(
                    f"[green][OK] Merge complete![/] Commit: [bold]{sha}[/]\n"
                    f"  Auto-resolved: {len(auto_resolved_files)} file(s)\n"
                    f"  Conflicts: 0",
                    title="Merge Result",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[yellow]Partial merge.[/]\n"
                    f"  Auto-resolved: {len(auto_resolved_files)} file(s)\n"
                    f"  [red]Conflicts remaining: {len(conflict_files)} file(s)[/]\n\n"
                    f"Run [bold]gc resolve[/] to interactively resolve remaining conflicts.",
                    title="Merge Result",
                    border_style="yellow",
                )
            )
    elif dry_run:
        console.print(
            Panel(
                f"[cyan]Dry run complete.[/]\n"
                f"  Would auto-resolve: {len(auto_resolved_files)} file(s)\n"
                f"  Would need manual: {len(conflict_files)} file(s)",
                title="Dry Run Result",
                border_style="cyan",
            )
        )
    else:
        console.print(
            Panel(
                f"[red]All {len(conflict_files)} file(s) have true conflicts.[/]\n"
                f"Run [bold]gc resolve[/] to interactively resolve them.",
                title="Merge Result",
                border_style="red",
            )
        )

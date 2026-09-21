"""gc release — Version management & changelog commands.

Subcommands:
  gc release plan  — Show recommended version bump and changelog preview
  gc release bump  — Apply the version bump and generate changelog
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from git_collab.core.git_ops import GitOps
from git_collab.versioning.commit_parser import parse_commit, categorize_commits, ConventionalCommit
from git_collab.versioning.semver import calculate_bump, SemVer
from git_collab.versioning.changelog import generate_changelog

console = Console(safe_box=True)

release_app = typer.Typer(
    name="release",
    help="Version management & changelog generation.",
    no_args_is_help=True,
)


@release_app.command(name="plan")
def release_plan(
    from_tag: str | None = typer.Option(None, "--from", "-f", help="Tag to compare from (default: latest tag)."),
) -> None:
    """Show recommended version bump and changelog preview.

    Analyzes commits since the last tag (or specified tag) and
    determines the correct SemVer bump based on conventional commits.
    """
    git = GitOps()

    # Find starting point
    if from_tag:
        tag = from_tag
    else:
        tag = git.get_latest_tag()
        if not tag:
            console.print("[yellow]No tags found.[/] Using first commit as baseline.")
            console.print("Create a tag first: [bold]git tag v0.1.0[/]")
            raise typer.Exit(1)

    console.print(f"[cyan]Analyzing commits since[/] [bold]{tag}[/] ...\n")

    # Get commits
    raw_commits = git.get_commits_between(tag, "HEAD")
    if not raw_commits:
        console.print("[green]No new commits since last tag.[/] Nothing to release.")
        return

    # Parse conventional commits
    parsed = []
    non_conventional = 0
    for c in raw_commits:
        result = parse_commit(c.message)
        if result:
            parsed.append(result)
        else:
            non_conventional += 1

    # Calculate bump
    decision = calculate_bump(tag, parsed)

    # Show commit summary table
    table = Table(title=f"Commits since {tag}", show_header=True, header_style="bold", safe_box=True)
    table.add_column("Type", style="cyan", width=10)
    table.add_column("Scope", style="dim", width=12)
    table.add_column("Description")
    table.add_column("Breaking", justify="center", width=10)

    for commit in parsed:
        breaking_mark = "[red][!] YES[/]" if commit.is_breaking else ""
        table.add_row(commit.type, commit.scope or "-", commit.description, breaking_mark)

    console.print(table)

    if non_conventional:
        console.print(f"\n[dim]({non_conventional} non-conventional commit(s) skipped)[/]")

    # Show bump decision
    bump_color = {"major": "red", "minor": "yellow", "patch": "green", "none": "dim"}
    color = bump_color.get(decision.bump_type, "white")

    console.print(
        Panel(
            f"Current version:     [bold]{decision.current}[/]\n"
            f"Recommended bump:    [{color}][bold]{decision.bump_type.upper()}[/][/]\n"
            f"Next version:        [{color}][bold]{decision.recommended}[/][/]\n\n"
            + "\n".join(f"  * {r}" for r in decision.reasons),
            title="Version Decision",
            border_style=color,
        )
    )

    # Show changelog preview
    changelog = generate_changelog(parsed, str(decision.recommended))
    console.print(Panel(changelog, title="Changelog Preview", border_style="cyan"))


@release_app.command(name="bump")
def release_bump(
    from_tag: str | None = typer.Option(None, "--from", "-f", help="Tag to compare from."),
    apply: bool = typer.Option(False, "--apply", "-a", help="Actually create the tag."),
) -> None:
    """Apply the recommended version bump and create a Git tag.

    Use --apply to actually create the tag. Without it, just shows
    what would happen (same as 'gc release plan').
    """
    git = GitOps()

    tag = from_tag or git.get_latest_tag()
    if not tag:
        console.print("[red]Error:[/] No tags found. Create one: [bold]git tag v0.1.0[/]")
        raise typer.Exit(1)

    raw_commits = git.get_commits_between(tag, "HEAD")
    parsed = [p for c in raw_commits if (p := parse_commit(c.message))]

    if not parsed:
        console.print("[green]No conventional commits to bump from.[/]")
        return

    decision = calculate_bump(tag, parsed)

    if decision.bump_type == "none":
        console.print("[green]No version bump needed.[/]")
        return

    if not apply:
        console.print(
            f"Would bump: [bold]{decision.current}[/] -> [bold]{decision.recommended}[/]\n"
            f"Run with [bold]--apply[/] to create the tag."
        )
        return

    # Create the tag
    new_tag = f"v{decision.recommended}"
    try:
        git.git.tag(new_tag)
        console.print(f"[green][OK] Created tag:[/] [bold]{new_tag}[/]")

        # Generate changelog
        changelog = generate_changelog(parsed, str(decision.recommended))
        console.print(Panel(changelog, title="Release Notes", border_style="green"))
    except Exception as e:
        console.print(f"[red]Error creating tag:[/] {e}")
        raise typer.Exit(1)

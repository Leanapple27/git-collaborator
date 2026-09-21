"""Main CLI entrypoint for git-collaborator (gc).

This is the root Typer application that registers all subcommands:
  gc merge     - AST-aware smart merge
  gc check     - Proactive conflict detection
  gc resolve   - Interactive TUI conflict resolver
  gc release   - Version management & changelog
  gc branch    - Branch health dashboard
"""

from __future__ import annotations

import sys

# Ensure UTF-8 output encoding on Windows terminals to prevent charmap errors
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import typer
from rich.console import Console

from git_collab.cli.merge_cmd import merge_cmd
from git_collab.cli.check_cmd import check_cmd
from git_collab.cli.resolve_cmd import resolve_cmd
from git_collab.cli.release_cmd import release_app
from git_collab.cli.branch_cmd import branch_cmd

app = typer.Typer(
    name="gc",
    help="git-collaborator - AST-aware Git collaboration & conflict resolution for Python.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console(safe_box=True)

# Register commands
app.command(name="merge", help="Smart AST-aware merge of a branch.")(merge_cmd)
app.command(name="check", help="Proactive conflict detection across branches.")(check_cmd)
app.command(name="resolve", help="Interactive TUI conflict resolver.")(resolve_cmd)
app.add_typer(release_app, name="release", help="Version management & changelog.")
app.command(name="branch", help="Branch health dashboard.")(branch_cmd)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """git-collaborator - smart Git for Python teams."""
    if ctx.invoked_subcommand is None:
        console.print(
            "[bold cyan]gc[/] - git-collaborator v0.1.0\n"
            "Run [bold]gc --help[/] to see available commands.",
        )


if __name__ == "__main__":
    app()

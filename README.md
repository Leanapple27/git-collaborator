# git-collaborator (gc)

**AST-aware Git collaboration & conflict resolution for Python projects.**

`git-collaborator` is a CLI + TUI tool that sits on top of Git, making collaborative Python development smarter. It understands Python's structure (functions, classes, imports) instead of just lines of text.

## Why?

Standard Git treats code as plain text. This means:
- Two developers adding **different imports** → unnecessary conflict
- Two developers editing **different functions** in the same file → false conflict
- A renamed function parameter breaks callers → undetected until runtime

`gc` solves these by using Python's `ast` module to understand code structure.

## Installation

```bash
cd git-collaborator
pip install -e ".[dev]"
```

## Commands

| Command | What It Does |
|---|---|
| `gc merge <branch>` | AST-aware merge — auto-resolves imports & independent functions |
| `gc check` | Proactively scans branches for potential conflicts |
| `gc resolve` | Interactive TUI for resolving real conflicts |
| `gc release plan` | Shows recommended version bump from commit messages |
| `gc release bump --apply` | Creates a Git tag with the calculated version |
| `gc branch` | Branch health dashboard (staleness, divergence) |

## Quick Start

```bash
# Check for potential conflicts across all branches
gc check

# Merge with AST-aware conflict resolution
gc merge feature-branch

# If conflicts remain, resolve interactively
gc resolve

# Plan a release
gc release plan
```

## How It Works

### Smart Import Merging
Parses Python `import` statements into structured data, computes the union across branches, removes duplicates, and sorts per PEP8.

### Independent Function Detection
Compares functions by **name** rather than by **line position**. If Branch A edits `func_a()` and Branch B adds `func_b()`, they merge cleanly — even if they're adjacent in the file.

### Proactive Conflict Detection
Before merging, analyzes which functions/classes each branch modified. If two branches touched the same symbol, you're warned immediately.

### Interactive TUI Resolver
Full-screen terminal UI with side-by-side OURS/THEIRS views, one-key resolution actions, and real-time Python syntax validation.

### Smart Version Bumps
Reads conventional commit messages (`feat:`, `fix:`, `feat!:`) and calculates the correct SemVer bump automatically.

## Running Tests

```bash
pytest tests/ -v
```

## Tech Stack

- **Python 3.10+** with built-in `ast` module
- **Typer** — CLI framework
- **Rich** — Terminal formatting
- **Textual** — TUI framework
- **GitPython** — Git operations

## License

MIT

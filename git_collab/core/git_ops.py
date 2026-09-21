"""Git operations wrapper — runs git commands and provides a clean Python interface.

This module wraps GitPython to provide high-level Git operations
needed by git-collaborator: branch management, diff extraction,
merge-base detection, and commit log retrieval.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from git import Repo, GitCommandError, InvalidGitRepositoryError


@dataclass
class BranchInfo:
    """Information about a Git branch."""

    name: str
    is_active: bool
    last_commit_sha: str
    last_commit_message: str
    last_commit_date: str
    commits_ahead: int = 0
    commits_behind: int = 0
    changed_files: list[str] = field(default_factory=list)


@dataclass
class CommitInfo:
    """Information about a single Git commit."""

    sha: str
    message: str
    author: str
    date: str


class GitOps:
    """High-level wrapper around Git operations.

    Provides methods for common Git tasks like listing branches,
    finding merge bases, extracting file versions, and running merges.

    Usage:
        git = GitOps("/path/to/repo")
        branches = git.list_branches()
        base = git.merge_base("main", "feature-branch")
    """

    def __init__(self, repo_path: str | Path | None = None) -> None:
        """Initialize GitOps with a repository path.

        Args:
            repo_path: Path to the Git repository. If None, uses current directory.

        Raises:
            SystemExit: If the path is not a valid Git repository.
        """
        path = Path(repo_path) if repo_path else Path.cwd()
        try:
            self.repo = Repo(path, search_parent_directories=True)
        except InvalidGitRepositoryError:
            raise SystemExit(f"Error: '{path}' is not a Git repository. Run 'git init' first.")
        self.git = self.repo.git

    @property
    def repo_root(self) -> Path:
        """Return the root directory of the repository."""
        return Path(self.repo.working_dir)

    @property
    def current_branch(self) -> str:
        """Return the name of the currently active branch."""
        return self.repo.active_branch.name

    # ── Branch Operations ──────────────────────────────────────────

    def list_branches(self, include_remote: bool = False) -> list[str]:
        """List all local branch names (optionally including remote tracking branches).

        Args:
            include_remote: If True, include remote tracking branches.

        Returns:
            List of branch name strings.
        """
        branches = [b.name for b in self.repo.branches]
        if include_remote:
            for ref in self.repo.remotes.origin.refs if self.repo.remotes else []:
                branches.append(ref.name)
        return branches

    def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists locally."""
        return branch_name in self.list_branches()

    def get_branch_info(self, branch_name: str, base_branch: str = "main") -> BranchInfo:
        """Get detailed information about a branch.

        Args:
            branch_name: Name of the branch to inspect.
            base_branch: Branch to compare against (default: main).

        Returns:
            BranchInfo with commit counts, last commit details, and changed files.
        """
        branch = self.repo.branches[branch_name]
        commit = branch.commit

        # Count commits ahead/behind relative to base
        ahead, behind = 0, 0
        if self.branch_exists(base_branch):
            merge_base_sha = self.merge_base(base_branch, branch_name)
            if merge_base_sha:
                ahead = int(self.git.rev_list("--count", f"{merge_base_sha}..{branch_name}"))
                behind = int(self.git.rev_list("--count", f"{merge_base_sha}..{base_branch}"))

        # Get changed files compared to base
        changed_files = []
        if self.branch_exists(base_branch):
            try:
                diff_output = self.git.diff("--name-only", base_branch, branch_name)
                changed_files = [f for f in diff_output.strip().split("\n") if f]
            except GitCommandError:
                pass

        return BranchInfo(
            name=branch_name,
            is_active=(branch_name == self.current_branch),
            last_commit_sha=commit.hexsha[:8],
            last_commit_message=commit.message.strip().split("\n")[0],
            last_commit_date=commit.committed_datetime.strftime("%Y-%m-%d %H:%M"),
            commits_ahead=ahead,
            commits_behind=behind,
            changed_files=changed_files,
        )

    # ── Merge & Diff Operations ────────────────────────────────────

    def merge_base(self, branch_a: str, branch_b: str) -> str | None:
        """Find the common ancestor commit of two branches.

        Args:
            branch_a: First branch name.
            branch_b: Second branch name.

        Returns:
            The SHA of the merge-base commit, or None if not found.
        """
        try:
            result = self.git.merge_base(branch_a, branch_b)
            return result.strip()
        except GitCommandError:
            return None

    def get_file_at_ref(self, ref: str, file_path: str) -> str | None:
        """Get the content of a file at a specific Git ref (commit, branch, tag).

        Args:
            ref: Git reference (e.g., branch name, commit SHA, tag).
            file_path: Path to the file relative to repo root.

        Returns:
            File content as string, or None if the file doesn't exist at that ref.
        """
        try:
            return self.git.show(f"{ref}:{file_path}")
        except GitCommandError:
            return None

    def get_changed_python_files(self, branch_a: str, branch_b: str) -> list[str]:
        """Get Python files that differ between two branches.

        Args:
            branch_a: First branch/ref.
            branch_b: Second branch/ref.

        Returns:
            List of .py file paths that changed between the two refs.
        """
        try:
            diff_output = self.git.diff("--name-only", "--diff-filter=ACMR", branch_a, branch_b)
            all_files = [f.strip() for f in diff_output.strip().split("\n") if f.strip()]
            return [f for f in all_files if f.endswith(".py")]
        except GitCommandError:
            return []

    def get_conflicted_files(self) -> list[str]:
        """Get list of files with unresolved merge conflicts.

        Returns:
            List of file paths that have merge conflicts.
        """
        try:
            status = self.git.status("--porcelain")
            conflicted = []
            for line in status.strip().split("\n"):
                if line and line[:2] in ("UU", "AA", "DD", "AU", "UA", "DU", "UD"):
                    conflicted.append(line[3:].strip())
            return conflicted
        except GitCommandError:
            return []

    # ── Commit Log Operations ──────────────────────────────────────

    def get_commits_between(self, from_ref: str, to_ref: str = "HEAD") -> list[CommitInfo]:
        """Get all commits between two refs.

        Args:
            from_ref: Starting ref (exclusive).
            to_ref: Ending ref (inclusive, default HEAD).

        Returns:
            List of CommitInfo objects.
        """
        try:
            log_output = self.git.log(
                f"{from_ref}..{to_ref}",
                "--format=%H||%s||%an||%ci",
                "--no-merges",
            )
            commits = []
            for line in log_output.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split("||", 3)
                if len(parts) == 4:
                    commits.append(CommitInfo(
                        sha=parts[0],
                        message=parts[1],
                        author=parts[2],
                        date=parts[3],
                    ))
            return commits
        except GitCommandError:
            return []

    def get_latest_tag(self) -> str | None:
        """Get the most recent tag in the repository.

        Returns:
            Tag name string, or None if no tags exist.
        """
        try:
            return self.git.describe("--tags", "--abbrev=0").strip()
        except GitCommandError:
            return None

    def get_all_tags(self) -> list[str]:
        """Get all tags in the repository, sorted by version.

        Returns:
            List of tag name strings.
        """
        try:
            output = self.git.tag("--sort=-version:refname")
            return [t.strip() for t in output.strip().split("\n") if t.strip()]
        except GitCommandError:
            return []

    # ── Staging & Commit ───────────────────────────────────────────

    def stage_file(self, file_path: str) -> None:
        """Stage a file for commit (git add).

        Args:
            file_path: Path to the file relative to repo root.
        """
        self.git.add(file_path)

    def commit(self, message: str) -> str:
        """Create a commit with the staged changes.

        Args:
            message: Commit message.

        Returns:
            SHA of the new commit.
        """
        self.git.commit("-m", message)
        return self.repo.head.commit.hexsha[:8]

    # ── Merge Helpers ──────────────────────────────────────────────

    def start_merge(self, branch_name: str, no_commit: bool = True) -> bool:
        """Start a merge without auto-committing.

        Args:
            branch_name: Branch to merge into the current branch.
            no_commit: If True, merge but don't auto-commit (default True).

        Returns:
            True if merge succeeded cleanly, False if there are conflicts.
        """
        try:
            args = ["--no-commit"] if no_commit else []
            self.git.merge(branch_name, *args)
            return True
        except GitCommandError:
            return False

    def abort_merge(self) -> None:
        """Abort an in-progress merge."""
        try:
            self.git.merge("--abort")
        except GitCommandError:
            pass

    def is_merge_in_progress(self) -> bool:
        """Check if a merge is currently in progress."""
        merge_head = self.repo_root / ".git" / "MERGE_HEAD"
        return merge_head.exists()

    def write_and_stage(self, file_path: str, content: str) -> None:
        """Write content to a file and stage it.

        Args:
            file_path: Path relative to repo root.
            content: New file content.
        """
        full_path = self.repo_root / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        self.stage_file(file_path)

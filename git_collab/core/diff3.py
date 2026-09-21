"""3-way file extraction for merge conflict resolution.

Extracts the BASE, OURS, and THEIRS versions of conflicted files
during a Git merge, providing clean content for the semantic merger.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from git_collab.core.git_ops import GitOps


@dataclass
class ThreeWayContent:
    """Holds the three versions of a file during a merge.

    Attributes:
        file_path: Path of the file relative to the repo root.
        base: Content from the common ancestor (merge-base).
        ours: Content from the current branch (HEAD).
        theirs: Content from the branch being merged.
    """

    file_path: str
    base: str
    ours: str
    theirs: str

    @property
    def is_python(self) -> bool:
        """Check if this file is a Python file."""
        return self.file_path.endswith(".py")


def extract_three_way(git: GitOps, file_path: str, their_branch: str) -> ThreeWayContent:
    """Extract BASE, OURS, and THEIRS content for a file during a merge.

    During an active merge conflict, Git stores stage entries:
      - Stage 1 = BASE (common ancestor)
      - Stage 2 = OURS (current branch / HEAD)
      - Stage 3 = THEIRS (branch being merged)

    This function extracts all three using `git show :N:path`.

    Args:
        git: GitOps instance for the repository.
        file_path: Path to the conflicted file relative to repo root.
        their_branch: Name of the branch being merged (used as fallback).

    Returns:
        ThreeWayContent with all three versions.

    Raises:
        ValueError: If file versions cannot be extracted.
    """
    # During a merge, stages 1/2/3 hold base/ours/theirs
    base = _get_stage(git, file_path, stage=1)
    ours = _get_stage(git, file_path, stage=2)
    theirs = _get_stage(git, file_path, stage=3)

    # Fallback: if stages aren't available (e.g., pre-merge analysis),
    # use branch refs directly
    if ours is None:
        ours = git.get_file_at_ref("HEAD", file_path) or ""
    if theirs is None:
        theirs = git.get_file_at_ref(their_branch, file_path) or ""
    if base is None:
        merge_base_sha = git.merge_base("HEAD", their_branch)
        base = git.get_file_at_ref(merge_base_sha, file_path) if merge_base_sha else ""
        base = base or ""

    return ThreeWayContent(
        file_path=file_path,
        base=base,
        ours=ours,
        theirs=theirs,
    )


def extract_three_way_from_refs(
    git: GitOps,
    file_path: str,
    base_ref: str,
    our_ref: str,
    their_ref: str,
) -> ThreeWayContent:
    """Extract BASE, OURS, THEIRS from explicit Git refs (no active merge needed).

    Useful for dry-run conflict analysis before actually merging.

    Args:
        git: GitOps instance.
        file_path: Path to the file relative to repo root.
        base_ref: Git ref for the base version.
        our_ref: Git ref for our version.
        their_ref: Git ref for their version.

    Returns:
        ThreeWayContent with all three versions.
    """
    return ThreeWayContent(
        file_path=file_path,
        base=git.get_file_at_ref(base_ref, file_path) or "",
        ours=git.get_file_at_ref(our_ref, file_path) or "",
        theirs=git.get_file_at_ref(their_ref, file_path) or "",
    )


def _get_stage(git: GitOps, file_path: str, stage: int) -> str | None:
    """Get file content at a specific merge stage.

    Args:
        git: GitOps instance.
        file_path: File path relative to repo root.
        stage: Merge stage (1=BASE, 2=OURS, 3=THEIRS).

    Returns:
        File content or None if stage doesn't exist.
    """
    try:
        return git.git.show(f":{stage}:{file_path}")
    except Exception:
        return None

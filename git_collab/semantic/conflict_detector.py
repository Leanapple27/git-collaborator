"""Proactive cross-branch conflict detection.

Scans branches BEFORE merging to detect which branches modify
the same Python symbols (functions, classes), warning developers
about potential merge conflicts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from git_collab.core.git_ops import GitOps
from git_collab.semantic.ast_parser import parse_module


@dataclass
class BranchChanges:
    """Symbols modified by a branch compared to the base."""

    branch_name: str
    modified_symbols: Dict[str, List[str]]  # file_path -> [symbol_names]
    files_changed: List[str]


@dataclass
class OverlapEntry:
    """A detected overlap between two branches."""

    branch_a: str
    branch_b: str
    file_path: str
    symbol_name: str
    risk: str  # 'HIGH', 'MEDIUM', 'LOW'


def get_branch_changes(git: GitOps, base_branch: str, feature_branch: str) -> BranchChanges:
    """Analyze which Python symbols a branch has modified relative to the base.

    Args:
        git: GitOps instance.
        base_branch: The base branch name (e.g., 'main').
        feature_branch: The feature branch to analyze.

    Returns:
        BranchChanges with modified symbols per file.
    """
    merge_base_sha = git.merge_base(base_branch, feature_branch)
    if not merge_base_sha:
        return BranchChanges(
            branch_name=feature_branch, modified_symbols={}, files_changed=[]
        )

    py_files = git.get_changed_python_files(merge_base_sha, feature_branch)

    modified_symbols: Dict[str, List[str]] = {}

    for f in py_files:
        base_src = git.get_file_at_ref(merge_base_sha, f)
        feat_src = git.get_file_at_ref(feature_branch, f)

        base_mod = parse_module(base_src) if base_src else None
        feat_mod = parse_module(feat_src) if feat_src else None

        # Build {name: source} dicts for comparison
        base_syms: Dict[str, str] = {}
        if base_mod:
            for s in base_mod.functions:
                base_syms[s.name] = s.source
            for s in base_mod.classes:
                base_syms[s.name] = s.source

        feat_syms: Dict[str, str] = {}
        if feat_mod:
            for s in feat_mod.functions:
                feat_syms[s.name] = s.source
            for s in feat_mod.classes:
                feat_syms[s.name] = s.source

        # Find modified, added, or deleted symbols
        mod_syms: List[str] = []
        for name, src in feat_syms.items():
            if name not in base_syms or base_syms[name] != src:
                mod_syms.append(name)
        # Also track deletions
        for name in base_syms:
            if name not in feat_syms:
                mod_syms.append(name)

        if mod_syms:
            modified_symbols[f] = mod_syms

    return BranchChanges(
        branch_name=feature_branch,
        modified_symbols=modified_symbols,
        files_changed=py_files,
    )


def detect_conflicts(
    git: GitOps,
    base_branch: str = "main",
    branches: Optional[List[str]] = None,
) -> List[OverlapEntry]:
    """Detect overlapping symbol modifications across branches.

    Compares every pair of feature branches to find symbols that
    were modified in both, indicating potential merge conflicts.

    Args:
        git: GitOps instance.
        base_branch: Base branch to compare against.
        branches: Specific branches to check (default: all local except base).

    Returns:
        List of OverlapEntry describing each detected overlap.
    """
    if branches is None:
        all_branches = git.list_branches()
        branches = [b for b in all_branches if b != base_branch]

    if not branches:
        return []

    # Analyze each branch
    branch_changes = [get_branch_changes(git, base_branch, b) for b in branches]

    # Compare every pair
    overlaps: List[OverlapEntry] = []
    for i in range(len(branch_changes)):
        for j in range(i + 1, len(branch_changes)):
            bc1 = branch_changes[i]
            bc2 = branch_changes[j]

            common_files = set(bc1.files_changed) & set(bc2.files_changed)
            for f in common_files:
                syms1 = set(bc1.modified_symbols.get(f, []))
                syms2 = set(bc2.modified_symbols.get(f, []))

                common_syms = syms1 & syms2

                if common_syms:
                    # Same symbol modified in both branches → HIGH risk
                    for s in common_syms:
                        overlaps.append(
                            OverlapEntry(
                                branch_a=bc1.branch_name,
                                branch_b=bc2.branch_name,
                                file_path=f,
                                symbol_name=s,
                                risk="HIGH",
                            )
                        )
                else:
                    # Same file but different symbols → MEDIUM risk
                    overlaps.append(
                        OverlapEntry(
                            branch_a=bc1.branch_name,
                            branch_b=bc2.branch_name,
                            file_path=f,
                            symbol_name="(different symbols)",
                            risk="MEDIUM",
                        )
                    )

    return overlaps

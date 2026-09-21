"""Tests for proactive conflict detection across branches."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from git import Repo

from git_collab.core.git_ops import GitOps
from git_collab.semantic.conflict_detector import detect_conflicts, get_branch_changes


class TestConflictDetector:
    """Test suite for cross-branch overlap detection."""

    def test_no_overlaps_independent_branches(self, repo_with_function_conflict: Repo) -> None:
        """Branches modifying different functions should have no HIGH risk overlaps."""
        repo = repo_with_function_conflict
        git = GitOps(repo.working_dir)
        overlaps = detect_conflicts(
            git,
            base_branch="main",
            branches=["branch-add-coupon", "branch-add-discount"],
        )
        # Both branches add to the same file, so we might get MEDIUM, but not HIGH
        high_risks = [o for o in overlaps if o.risk == "HIGH"]
        assert len(high_risks) == 0

    def test_overlapping_function_modification(self, repo_with_true_conflict: Repo) -> None:
        """Branches modifying the same function should be HIGH risk."""
        repo = repo_with_true_conflict
        git = GitOps(repo.working_dir)
        overlaps = detect_conflicts(
            git,
            base_branch="main",
            branches=["branch-tax-rate", "branch-tax-param"],
        )
        high_risks = [o for o in overlaps if o.risk == "HIGH"]
        assert len(high_risks) >= 1
        assert any("calculate_tax" in o.symbol_name for o in high_risks)

    def test_get_branch_changes(self, repo_with_function_conflict: Repo) -> None:
        """get_branch_changes should detect added functions."""
        repo = repo_with_function_conflict
        git = GitOps(repo.working_dir)
        changes = get_branch_changes(git, "main", "branch-add-coupon")
        assert len(changes.files_changed) > 0
        # Should detect validate_coupon as a modified symbol
        all_symbols = []
        for syms in changes.modified_symbols.values():
            all_symbols.extend(syms)
        assert "validate_coupon" in all_symbols

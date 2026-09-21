"""Tests for the conventional commit parser and SemVer calculator."""

from __future__ import annotations

from git_collab.versioning.commit_parser import parse_commit, parse_commits, categorize_commits
from git_collab.versioning.semver import SemVer, calculate_bump


class TestCommitParser:
    """Test suite for conventional commit parsing."""

    def test_simple_feat(self) -> None:
        result = parse_commit("feat: add login page")
        assert result is not None
        assert result.type == "feat"
        assert result.description == "add login page"
        assert result.scope is None
        assert not result.is_breaking

    def test_fix_with_scope(self) -> None:
        result = parse_commit("fix(auth): handle null token")
        assert result is not None
        assert result.type == "fix"
        assert result.scope == "auth"
        assert result.description == "handle null token"

    def test_breaking_with_bang(self) -> None:
        result = parse_commit("feat!: redesign API")
        assert result is not None
        assert result.is_breaking

    def test_breaking_with_scope_and_bang(self) -> None:
        result = parse_commit("feat(api)!: remove endpoint")
        assert result is not None
        assert result.is_breaking
        assert result.scope == "api"

    def test_breaking_in_body(self) -> None:
        result = parse_commit("feat: change auth\n\nBREAKING CHANGE: removed password field")
        assert result is not None
        assert result.is_breaking

    def test_non_conventional_returns_none(self) -> None:
        result = parse_commit("Updated the readme file")
        assert result is None

    def test_parse_commits_skips_invalid(self) -> None:
        messages = [
            "feat: add login",
            "random commit message",
            "fix: handle error",
        ]
        results = parse_commits(messages)
        assert len(results) == 2

    def test_categorize_commits(self) -> None:
        commits = parse_commits([
            "feat: add search",
            "fix: handle null",
            "feat!: break stuff",
            "docs: update readme",
        ])
        cats = categorize_commits(commits)
        assert len(cats["features"]) == 1
        assert len(cats["fixes"]) == 1
        assert len(cats["breaking"]) == 1
        assert len(cats["other"]) == 1


class TestSemVer:
    """Test suite for semantic versioning."""

    def test_parse_version(self) -> None:
        v = SemVer.from_string("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_parse_with_v_prefix(self) -> None:
        v = SemVer.from_string("v2.0.1")
        assert v.major == 2
        assert str(v) == "2.0.1"

    def test_bump_major(self) -> None:
        v = SemVer(1, 2, 3)
        bumped = v.bump_major()
        assert str(bumped) == "2.0.0"

    def test_bump_minor(self) -> None:
        v = SemVer(1, 2, 3)
        bumped = v.bump_minor()
        assert str(bumped) == "1.3.0"

    def test_bump_patch(self) -> None:
        v = SemVer(1, 2, 3)
        bumped = v.bump_patch()
        assert str(bumped) == "1.2.4"

    def test_calculate_bump_breaking(self) -> None:
        commits = parse_commits(["feat!: break API", "fix: small fix"])
        decision = calculate_bump("v1.0.0", commits)
        assert decision.bump_type == "major"
        assert str(decision.recommended) == "2.0.0"

    def test_calculate_bump_feature(self) -> None:
        commits = parse_commits(["feat: add feature", "fix: bug fix"])
        decision = calculate_bump("v1.0.0", commits)
        assert decision.bump_type == "minor"
        assert str(decision.recommended) == "1.1.0"

    def test_calculate_bump_patch(self) -> None:
        commits = parse_commits(["fix: bug fix"])
        decision = calculate_bump("v1.0.0", commits)
        assert decision.bump_type == "patch"
        assert str(decision.recommended) == "1.0.1"

    def test_calculate_bump_none(self) -> None:
        commits = parse_commits(["docs: update readme"])
        decision = calculate_bump("v1.0.0", commits)
        assert decision.bump_type == "none"

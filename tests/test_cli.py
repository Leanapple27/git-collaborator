"""End-to-end CLI command tests."""

from __future__ import annotations

from typer.testing import CliRunner

from git_collab.cli.main import app

runner = CliRunner()


class TestCLI:
    """Test the CLI commands respond correctly."""

    def test_help_shows_commands(self) -> None:
        """gc --help should list all available commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "merge" in result.output
        assert "check" in result.output
        assert "resolve" in result.output
        assert "release" in result.output
        assert "branch" in result.output

    def test_merge_requires_branch_arg(self) -> None:
        """gc merge without a branch name should show an error."""
        result = runner.invoke(app, ["merge"])
        # Should error or show help since branch argument is required
        assert result.exit_code != 0 or "Missing" in result.output or "Usage" in result.output

    def test_release_plan_no_repo(self) -> None:
        """gc release plan outside a git repo should error gracefully."""
        result = runner.invoke(app, ["release", "plan"])
        # Should show an error about not being in a git repo
        assert result.exit_code != 0 or "Error" in result.output or "not a Git repository" in result.output

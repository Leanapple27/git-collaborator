"""Pytest fixtures for git-collaborator tests.

Provides temporary Git repositories with branches, commits, and
conflicts for testing the semantic merge engine and CLI commands.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest
from git import Repo


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Repo:
    """Create a temporary Git repository with an initial commit.

    Returns:
        A GitPython Repo object rooted at tmp_path.
    """
    repo = Repo.init(tmp_path, initial_branch="main")

    # Configure git user for commits
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Create initial file and commit
    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    return repo


@pytest.fixture
def repo_with_python_file(tmp_repo: Repo) -> Repo:
    """Create a repo with a base Python file on main.

    The file contains imports, functions, and a class for testing merges.
    """
    root = Path(tmp_repo.working_dir)

    base_code = textwrap.dedent('''\
        import os
        import sys

        from pathlib import Path


        def calculate_tax(amount):
            """Calculate tax for a given amount."""
            return amount * 0.1


        def format_currency(value):
            """Format a value as currency string."""
            return f"${value:.2f}"


        class OrderProcessor:
            """Processes customer orders."""

            def __init__(self, order_id):
                self.order_id = order_id

            def process(self):
                """Process the order."""
                return f"Order {self.order_id} processed"
    ''')

    py_file = root / "calculator.py"
    py_file.write_text(base_code)
    tmp_repo.index.add(["calculator.py"])
    tmp_repo.index.commit("Add calculator module")

    return tmp_repo


@pytest.fixture
def repo_with_import_conflict(repo_with_python_file: Repo) -> Repo:
    """Create a repo with conflicting imports on two branches.

    Branch A adds: from collections import OrderedDict
    Branch B adds: from collections import defaultdict
    Both touch the import region, causing a standard git conflict.
    """
    repo = repo_with_python_file
    root = Path(repo.working_dir)
    py_file = root / "calculator.py"

    # Read base content
    base_content = py_file.read_text()

    # Create branch A
    repo.create_head("feature-a")
    repo.heads["feature-a"].checkout()

    new_content_a = base_content.replace(
        "from pathlib import Path",
        "from collections import OrderedDict\nfrom pathlib import Path",
    )
    py_file.write_text(new_content_a)
    repo.index.add(["calculator.py"])
    repo.index.commit("feat: add OrderedDict import")

    # Go back to main
    repo.heads.main.checkout()

    # Create branch B
    repo.create_head("feature-b")
    repo.heads["feature-b"].checkout()

    new_content_b = base_content.replace(
        "from pathlib import Path",
        "from collections import defaultdict\nfrom pathlib import Path",
    )
    py_file.write_text(new_content_b)
    repo.index.add(["calculator.py"])
    repo.index.commit("feat: add defaultdict import")

    # Go back to main
    repo.heads.main.checkout()

    return repo


@pytest.fixture
def repo_with_function_conflict(repo_with_python_file: Repo) -> Repo:
    """Create a repo where two branches add different functions.

    Branch A adds: validate_coupon()
    Branch B adds: apply_discount()
    These are independent and should be auto-merged.
    """
    repo = repo_with_python_file
    root = Path(repo.working_dir)
    py_file = root / "calculator.py"

    base_content = py_file.read_text()

    # Create branch A — adds validate_coupon
    repo.create_head("branch-add-coupon")
    repo.heads["branch-add-coupon"].checkout()

    content_a = base_content + textwrap.dedent('''

        def validate_coupon(code):
            """Check if a coupon code is valid."""
            valid_codes = ["SAVE10", "SAVE20", "WELCOME"]
            return code.upper() in valid_codes
    ''')
    py_file.write_text(content_a)
    repo.index.add(["calculator.py"])
    repo.index.commit("feat: add coupon validation")

    # Go back to main
    repo.heads.main.checkout()

    # Create branch B — adds apply_discount
    repo.create_head("branch-add-discount")
    repo.heads["branch-add-discount"].checkout()

    content_b = base_content + textwrap.dedent('''

        def apply_discount(price, percent):
            """Apply a percentage discount to a price."""
            return price * (1 - percent / 100)
    ''')
    py_file.write_text(content_b)
    repo.index.add(["calculator.py"])
    repo.index.commit("feat: add discount function")

    # Go back to main
    repo.heads.main.checkout()

    return repo


@pytest.fixture
def repo_with_true_conflict(repo_with_python_file: Repo) -> Repo:
    """Create a repo where two branches modify the SAME function differently.

    Branch A changes calculate_tax to use 15% rate.
    Branch B changes calculate_tax to add a 'rate' parameter.
    This is a true conflict that cannot be auto-resolved.
    """
    repo = repo_with_python_file
    root = Path(repo.working_dir)
    py_file = root / "calculator.py"

    base_content = py_file.read_text()

    # Branch A — changes tax rate to 15%
    repo.create_head("branch-tax-rate")
    repo.heads["branch-tax-rate"].checkout()

    content_a = base_content.replace(
        "return amount * 0.1",
        "return amount * 0.15  # Updated tax rate",
    )
    py_file.write_text(content_a)
    repo.index.add(["calculator.py"])
    repo.index.commit("fix: update tax rate to 15%")

    # Go back to main
    repo.heads.main.checkout()

    # Branch B — adds rate parameter
    repo.create_head("branch-tax-param")
    repo.heads["branch-tax-param"].checkout()

    content_b = base_content.replace(
        "def calculate_tax(amount):",
        "def calculate_tax(amount, rate=0.1):",
    ).replace(
        "return amount * 0.1",
        "return amount * rate",
    )
    py_file.write_text(content_b)
    repo.index.add(["calculator.py"])
    repo.index.commit("feat: make tax rate configurable")

    # Go back to main
    repo.heads.main.checkout()

    return repo


@pytest.fixture
def repo_with_conventional_commits(tmp_repo: Repo) -> Repo:
    """Create a repo with conventional commit messages and a base tag.

    Commits include feat, fix, feat!, and regular (non-conventional) messages.
    """
    repo = tmp_repo
    root = Path(repo.working_dir)

    # Create base tag
    repo.create_tag("v1.0.0")

    # Add conventional commits
    messages = [
        ("feat: add user authentication", "auth.py"),
        ("fix: handle null token in session", "session.py"),
        ("feat(ui): add dark mode toggle", "ui.py"),
        ("docs: update README", "docs.md"),
        ("feat!: redesign user API", "api.py"),
        ("fix(db): prevent SQL injection", "db.py"),
        ("chore: update dependencies", "deps.txt"),
    ]

    for msg, filename in messages:
        f = root / filename
        f.write_text(f"# {filename}\n")
        repo.index.add([filename])
        repo.index.commit(msg)

    return repo

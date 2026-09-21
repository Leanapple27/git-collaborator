"""Demo setup script for git-collaborator presentation.

Run this ONCE before the demo to create a sample project with
branches that demonstrate each feature.

Usage:
    python demo_setup.py

This creates a folder 'demo-project' with a git repo containing:
  - main branch with a Python calculator module
  - feature-auth branch (adds auth imports + login function)
  - feature-payments branch (adds payment imports + payment function)
  - feature-tax-v1 branch (changes tax rate to 15%)
  - feature-tax-v2 branch (makes tax rate a parameter)
  - Conventional commits for release demo
"""

from __future__ import annotations

import os
import shutil
import textwrap
from pathlib import Path

from git import Repo


DEMO_DIR = Path(__file__).parent / "demo-project"


def setup_demo() -> None:
    """Create the demo repository with all branches."""

    # Clean previous demo
    if DEMO_DIR.exists():
        # On Windows, need to handle git's read-only files
        def force_remove(path, onerror=None):
            import stat
            for root, dirs, files in os.walk(path, topdown=False):
                for f in files:
                    fp = os.path.join(root, f)
                    os.chmod(fp, stat.S_IWRITE)
                    os.remove(fp)
                for d in dirs:
                    dp = os.path.join(root, d)
                    os.chmod(dp, stat.S_IWRITE)
                    os.rmdir(dp)
            os.rmdir(path)
        force_remove(str(DEMO_DIR))

    DEMO_DIR.mkdir()

    # Initialize repo
    repo = Repo.init(DEMO_DIR, initial_branch="main")
    repo.config_writer().set_value("user", "name", "Demo User").release()
    repo.config_writer().set_value("user", "email", "demo@example.com").release()

    # ── STEP 1: Base project on main ─────────────────────────────
    calculator = DEMO_DIR / "calculator.py"
    calculator.write_text(textwrap.dedent('''\
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
    '''))

    utils = DEMO_DIR / "utils.py"
    utils.write_text(textwrap.dedent('''\
        def validate_email(email):
            """Check if email format is valid."""
            return "@" in email and "." in email


        def sanitize_input(text):
            """Remove dangerous characters from input."""
            return text.replace("<", "").replace(">", "")
    '''))

    repo.index.add(["calculator.py", "utils.py"])
    repo.index.commit("Initial commit: add calculator and utils")

    # Tag v1.0.0
    repo.create_tag("v1.0.0")

    # ── STEP 2: feature-auth branch (IMPORT CONFLICT demo) ──────
    repo.create_head("feature-auth")
    repo.heads["feature-auth"].checkout()

    # Add auth-related import AND a new function
    auth_content = calculator.read_text().replace(
        "from pathlib import Path",
        "from collections import OrderedDict\nfrom pathlib import Path",
    )
    auth_content += textwrap.dedent('''

        def authenticate_user(username, password):
            """Authenticate a user with username and password."""
            # Simple demo authentication
            valid_users = {"admin": "secret", "user": "pass123"}
            return valid_users.get(username) == password
    ''')
    calculator.write_text(auth_content)
    repo.index.add(["calculator.py"])
    repo.index.commit("feat(auth): add user authentication")

    repo.heads.main.checkout()

    # ── STEP 3: feature-payments branch (IMPORT CONFLICT demo) ──
    repo.create_head("feature-payments")
    repo.heads["feature-payments"].checkout()

    # Add payment-related import AND a new function
    pay_content = calculator.read_text().replace(
        "from pathlib import Path",
        "from collections import defaultdict\nfrom pathlib import Path",
    )
    pay_content += textwrap.dedent('''

        def process_payment(amount, method="card"):
            """Process a payment with the given method."""
            fee = amount * 0.02 if method == "card" else 0
            return amount + fee
    ''')
    calculator.write_text(pay_content)
    repo.index.add(["calculator.py"])
    repo.index.commit("feat(payments): add payment processing")

    repo.heads.main.checkout()

    # ── STEP 4: feature-tax-v1 branch (TRUE CONFLICT demo) ──────
    repo.create_head("feature-tax-v1")
    repo.heads["feature-tax-v1"].checkout()

    tax1_content = calculator.read_text().replace(
        "return amount * 0.1",
        "return amount * 0.15  # Updated to 15% tax",
    )
    calculator.write_text(tax1_content)
    repo.index.add(["calculator.py"])
    repo.index.commit("fix: update tax rate to 15%")

    repo.heads.main.checkout()

    # ── STEP 5: feature-tax-v2 branch (TRUE CONFLICT demo) ──────
    repo.create_head("feature-tax-v2")
    repo.heads["feature-tax-v2"].checkout()

    tax2_content = calculator.read_text().replace(
        "def calculate_tax(amount):",
        "def calculate_tax(amount, rate=0.1):",
    ).replace(
        "return amount * 0.1",
        "return amount * rate  # Configurable tax rate",
    )
    calculator.write_text(tax2_content)
    repo.index.add(["calculator.py"])
    repo.index.commit("feat: make tax rate configurable")

    repo.heads.main.checkout()

    # ── STEP 6: Add conventional commits for release demo ────────
    commits_for_release = [
        ("feat: add user authentication", "auth.py"),
        ("fix: handle null token in session", "session.py"),
        ("feat(ui): add dark mode toggle", "ui.py"),
        ("fix(db): prevent SQL injection", "db.py"),
        ("feat!: redesign user API", "api.py"),
        ("chore: update dependencies", "deps.txt"),
    ]

    for msg, filename in commits_for_release:
        f = DEMO_DIR / filename
        f.write_text(f"# {filename}\n# Demo file\n")
        repo.index.add([filename])
        repo.index.commit(msg)

    print("=" * 60)
    print("  DEMO PROJECT READY!")
    print("=" * 60)
    print(f"\n  Location: {DEMO_DIR}")
    print(f"\n  Branches created:")
    for b in repo.branches:
        marker = " <-- (active)" if b.name == repo.active_branch.name else ""
        print(f"    - {b.name}{marker}")
    print(f"\n  Tag: v1.0.0")
    print(f"\n  Run the demo from: {DEMO_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    setup_demo()

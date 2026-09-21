"""Tests for the import merger — verifying auto-resolution of import conflicts."""

from __future__ import annotations

import textwrap

from git_collab.semantic.import_merger import merge_imports, format_imports


class TestImportMerger:
    """Test suite for smart import merging."""

    def test_no_conflict_same_imports(self) -> None:
        """When all three versions have the same imports, no changes needed."""
        src = "import os\nimport sys\n"
        result = merge_imports(src, src, src)
        assert not result.had_conflicts
        assert len(result.merged_imports) == 2

    def test_ours_adds_import(self) -> None:
        """When only our branch adds an import, it should be included."""
        base = "import os\n"
        ours = "import os\nimport json\n"
        theirs = "import os\n"
        result = merge_imports(base, ours, theirs)
        assert not result.had_conflicts
        formatted = format_imports(result.merged_imports)
        assert "import json" in formatted
        assert "import os" in formatted

    def test_theirs_adds_import(self) -> None:
        """When only their branch adds an import, it should be included."""
        base = "import os\n"
        ours = "import os\n"
        theirs = "import os\nimport re\n"
        result = merge_imports(base, ours, theirs)
        assert not result.had_conflicts
        formatted = format_imports(result.merged_imports)
        assert "import re" in formatted

    def test_both_add_different_imports(self) -> None:
        """When both branches add different imports, union them."""
        base = "import os\n"
        ours = "import os\nimport json\n"
        theirs = "import os\nimport re\n"
        result = merge_imports(base, ours, theirs)
        assert not result.had_conflicts
        formatted = format_imports(result.merged_imports)
        assert "import json" in formatted
        assert "import re" in formatted
        assert "import os" in formatted

    def test_both_add_same_import(self) -> None:
        """When both branches add the same import, deduplicate."""
        base = "import os\n"
        ours = "import os\nimport json\n"
        theirs = "import os\nimport json\n"
        result = merge_imports(base, ours, theirs)
        assert not result.had_conflicts
        formatted = format_imports(result.merged_imports)
        assert formatted.count("import json") == 1

    def test_from_imports_merged(self) -> None:
        """From-style imports from different modules are merged."""
        base = "from pathlib import Path\n"
        ours = "from pathlib import Path\nfrom collections import OrderedDict\n"
        theirs = "from pathlib import Path\nfrom collections import defaultdict\n"
        result = merge_imports(base, ours, theirs)
        assert not result.had_conflicts
        formatted = format_imports(result.merged_imports)
        assert "OrderedDict" in formatted
        assert "defaultdict" in formatted

    def test_import_removed_by_ours(self) -> None:
        """When our branch removes an import, it stays removed."""
        base = "import os\nimport sys\n"
        ours = "import os\n"
        theirs = "import os\nimport sys\n"
        result = merge_imports(base, ours, theirs)
        formatted = format_imports(result.merged_imports)
        assert "import sys" not in formatted

    def test_stdlib_sorted_first(self) -> None:
        """Stdlib imports should appear before third-party imports."""
        base = ""
        ours = "import requests\n"
        theirs = "import os\n"
        result = merge_imports(base, ours, theirs)
        formatted = format_imports(result.merged_imports)
        lines = formatted.strip().split("\n")
        # os (stdlib) should come before requests (third-party)
        os_idx = next(i for i, l in enumerate(lines) if "import os" in l)
        req_idx = next(i for i, l in enumerate(lines) if "import requests" in l)
        assert os_idx < req_idx

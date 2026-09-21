"""Tests for the function merger — verifying independent function detection and true conflicts."""

from __future__ import annotations

import textwrap

from git_collab.semantic.function_merger import merge_functions


class TestFunctionMerger:
    """Test suite for AST-based function/class merging."""

    def test_independent_function_additions(self) -> None:
        """Two branches adding different functions should auto-merge."""
        base = textwrap.dedent('''\
            def existing():
                return 1
        ''')
        ours = textwrap.dedent('''\
            def existing():
                return 1

            def func_a():
                return "a"
        ''')
        theirs = textwrap.dedent('''\
            def existing():
                return 1

            def func_b():
                return "b"
        ''')
        result = merge_functions(base, ours, theirs)
        assert len(result.conflicts) == 0
        assert "func_a" in result.merged_source
        assert "func_b" in result.merged_source
        assert "existing" in result.merged_source

    def test_same_function_modified_differently_is_conflict(self) -> None:
        """Both branches modifying the same function differently = true conflict."""
        base = textwrap.dedent('''\
            def calculate(x):
                return x * 2
        ''')
        ours = textwrap.dedent('''\
            def calculate(x):
                return x * 3
        ''')
        theirs = textwrap.dedent('''\
            def calculate(x):
                return x + 10
        ''')
        result = merge_functions(base, ours, theirs)
        assert len(result.conflicts) == 1
        assert result.conflicts[0].name == "calculate"

    def test_same_modification_both_branches(self) -> None:
        """Both branches making identical changes should auto-resolve."""
        base = textwrap.dedent('''\
            def greet():
                return "hello"
        ''')
        ours = textwrap.dedent('''\
            def greet():
                return "hello world"
        ''')
        theirs = textwrap.dedent('''\
            def greet():
                return "hello world"
        ''')
        result = merge_functions(base, ours, theirs)
        assert len(result.conflicts) == 0
        assert "hello world" in result.merged_source

    def test_only_ours_modifies(self) -> None:
        """When only our branch modifies a function, take ours."""
        base = textwrap.dedent('''\
            def process(x):
                return x
        ''')
        ours = textwrap.dedent('''\
            def process(x):
                return x * 2
        ''')
        theirs = textwrap.dedent('''\
            def process(x):
                return x
        ''')
        result = merge_functions(base, ours, theirs)
        assert len(result.conflicts) == 0
        assert "x * 2" in result.merged_source

    def test_only_theirs_modifies(self) -> None:
        """When only their branch modifies a function, take theirs."""
        base = textwrap.dedent('''\
            def process(x):
                return x
        ''')
        ours = textwrap.dedent('''\
            def process(x):
                return x
        ''')
        theirs = textwrap.dedent('''\
            def process(x):
                return x + 1
        ''')
        result = merge_functions(base, ours, theirs)
        assert len(result.conflicts) == 0
        assert "x + 1" in result.merged_source

    def test_class_additions_merged(self) -> None:
        """Two branches adding different classes should auto-merge."""
        base = ""
        ours = textwrap.dedent('''\
            class Dog:
                def bark(self):
                    return "woof"
        ''')
        theirs = textwrap.dedent('''\
            class Cat:
                def meow(self):
                    return "meow"
        ''')
        result = merge_functions(base, ours, theirs)
        assert len(result.conflicts) == 0
        assert "Dog" in result.merged_source
        assert "Cat" in result.merged_source

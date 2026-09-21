from __future__ import annotations
import difflib
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

class DiffPanel(Static):
    """A panel that displays content with highlighted differences."""
    
    def __init__(self, content: str, title: str, changes: list[tuple[str, str]] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.content = content
        self.title_text = title
        self.changes = changes or []

    def on_mount(self) -> None:
        self.border_title = self.title_text
        self.update_content()

    def update_content(self) -> None:
        text = Text()
        for tag, line in self.changes:
            if tag == "insert":
                text.append(line, style="black on green")
            elif tag == "delete":
                text.append(line, style="white on red")
            elif tag == "equal":
                text.append(line)
        if not self.changes:
            # If no changes provided, just show the content
            text = Text(self.content)
        self.update(text)


class DiffView(Static):
    """A widget that displays a side-by-side diff view of two text contents."""
    
    def __init__(self, left_content: str, right_content: str, left_title: str = "Left", right_title: str = "Right", **kwargs) -> None:
        super().__init__(**kwargs)
        self.left_content = left_content
        self.right_content = right_content
        self.left_title = left_title
        self.right_title = right_title

    def compose(self) -> ComposeResult:
        left_changes, right_changes = self._compute_diff(self.left_content, self.right_content)
        
        with Horizontal():
            yield DiffPanel(self.left_content, title=self.left_title, changes=left_changes, id="left-panel", classes="diff-panel")
            yield DiffPanel(self.right_content, title=self.right_title, changes=right_changes, id="right-panel", classes="diff-panel")

    def _compute_diff(self, left: str, right: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        left_lines = left.splitlines(keepends=True)
        right_lines = right.splitlines(keepends=True)
        
        matcher = difflib.SequenceMatcher(None, left_lines, right_lines)
        
        left_changes = []
        right_changes = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                for line in left_lines[i1:i2]:
                    left_changes.append(("delete", line))
                for line in right_lines[j1:j2]:
                    right_changes.append(("insert", line))
            elif tag == "delete":
                for line in left_lines[i1:i2]:
                    left_changes.append(("delete", line))
            elif tag == "insert":
                for line in right_lines[j1:j2]:
                    right_changes.append(("insert", line))
            elif tag == "equal":
                for line in left_lines[i1:i2]:
                    left_changes.append(("equal", line))
                    right_changes.append(("equal", line))
                    
        return left_changes, right_changes

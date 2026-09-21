from __future__ import annotations
import difflib
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, TextArea, Label
from textual.binding import Binding

from git_collab.tui.diff_view import DiffPanel
from git_collab.tui.status_bar import StatusBar, validate_python

class ResolverApp(App):
    """Interactive TUI application for resolving git conflicts."""
    
    CSS = """
    .diff-panel {
        width: 1fr;
        height: 1fr;
        border: solid green;
    }
    #result-area {
        height: 1fr;
        border: solid blue;
    }
    StatusBar {
        height: 1;
        dock: bottom;
        background: $boost;
    }
    """

    BINDINGS = [
        Binding("o", "accept_ours", "Accept Ours"),
        Binding("t", "accept_theirs", "Accept Theirs"),
        Binding("b", "accept_both", "Accept Both"),
        Binding("s", "save_and_exit", "Save & Exit"),
        Binding("q", "quit_no_save", "Quit"),
        Binding("v", "validate", "Validate Syntax"),
    ]

    def __init__(self, ours_content: str, theirs_content: str, file_path: str, **kwargs) -> None:
        """Initialize the app with contents and file path.
        
        Args:
            ours_content (str): Content of our version.
            theirs_content (str): Content of their version.
            file_path (str): The file path being resolved.
        """
        super().__init__(**kwargs)
        self.ours_content = ours_content
        self.theirs_content = theirs_content
        self.file_path = file_path
        self.resolved_content: str | None = None
        self.current_mode = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        # Compute changes for DiffPanel
        ours_lines = self.ours_content.splitlines(keepends=True)
        theirs_lines = self.theirs_content.splitlines(keepends=True)
        matcher = difflib.SequenceMatcher(None, ours_lines, theirs_lines)
        ours_changes = []
        theirs_changes = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                for line in ours_lines[i1:i2]: ours_changes.append(("delete", line))
                for line in theirs_lines[j1:j2]: theirs_changes.append(("insert", line))
            elif tag == "delete":
                for line in ours_lines[i1:i2]: ours_changes.append(("delete", line))
            elif tag == "insert":
                for line in theirs_lines[j1:j2]: theirs_changes.append(("insert", line))
            elif tag == "equal":
                for line in ours_lines[i1:i2]: 
                    ours_changes.append(("equal", line))
                    theirs_changes.append(("equal", line))

        with Vertical():
            with Horizontal():
                yield DiffPanel(self.ours_content, title="OURS", changes=ours_changes, classes="diff-panel")
                yield DiffPanel(self.theirs_content, title="THEIRS", changes=theirs_changes, classes="diff-panel")
            
            yield Label("─── RESULT ───")
            yield TextArea(self.ours_content, id="result-area")
        
        yield StatusBar()
        yield Footer()

    def on_mount(self) -> None:
        self.title = "git-collaborator — Conflict Resolver"
        self._validate_and_update_status()

    def _validate_and_update_status(self) -> None:
        text_area = self.query_one("#result-area", TextArea)
        is_valid, error_msg = validate_python(text_area.text)
        status_bar = self.query_one(StatusBar)
        status_bar.update_status(self.file_path, is_valid, error_msg, self.current_mode)

    def action_accept_ours(self) -> None:
        text_area = self.query_one("#result-area", TextArea)
        text_area.text = self.ours_content
        self.current_mode = "Ours"
        self._validate_and_update_status()

    def action_accept_theirs(self) -> None:
        text_area = self.query_one("#result-area", TextArea)
        text_area.text = self.theirs_content
        self.current_mode = "Theirs"
        self._validate_and_update_status()

    def action_accept_both(self) -> None:
        text_area = self.query_one("#result-area", TextArea)
        text_area.text = self.ours_content + "\n# --- THEIRS ---\n" + self.theirs_content
        self.current_mode = "Both"
        self._validate_and_update_status()

    def action_validate(self) -> None:
        self.current_mode = "Custom"
        self._validate_and_update_status()

    def action_save_and_exit(self) -> None:
        text_area = self.query_one("#result-area", TextArea)
        self.resolved_content = text_area.text
        self.exit(self.resolved_content)

    def action_quit_no_save(self) -> None:
        self.resolved_content = None
        self.exit(None)

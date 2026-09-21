from __future__ import annotations
import ast
from rich.text import Text
from textual.widgets import Static

def validate_python(source: str) -> tuple[bool, str]:
    """Validate Python source code.
    
    Args:
        source (str): The Python source code to validate.

    Returns:
        tuple[bool, str]: (True, '') if valid, (False, error_message) if invalid.
    """
    try:
        ast.parse(source)
        return True, ""
    except SyntaxError as e:
        return False, str(e)


class StatusBar(Static):
    """A status bar widget displaying current file, validation status, and mode."""
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.file_path = ""
        self.is_valid = True
        self.error_msg = ""
        self.mode = ""

    def on_mount(self) -> None:
        self.refresh_status()

    def update_status(self, file_path: str, is_valid: bool, error_msg: str = "", mode: str = "") -> None:
        """Update the status bar information.
        
        Args:
            file_path (str): The current file being resolved.
            is_valid (bool): Whether the current result is valid Python.
            error_msg (str): Error message if not valid.
            mode (str): Resolution mode (Ours, Theirs, Both, Custom).
        """
        self.file_path = file_path
        self.is_valid = is_valid
        self.error_msg = error_msg
        self.mode = mode
        self.refresh_status()

    def refresh_status(self) -> None:
        text = Text()
        text.append(f" File: {self.file_path} | ", style="bold")
        
        if self.is_valid:
            text.append("✅ Valid Python", style="green")
        else:
            text.append(f"❌ Syntax Error: {self.error_msg}", style="red")
            
        text.append(f" | Mode: {self.mode or 'None'} ", style="bold")
        
        self.update(text)

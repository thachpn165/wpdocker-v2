"""
Text editor utilities.

This module provides functionality for selecting and working with
text editors available on the system.
"""

import shutil
from typing import Dict, List, Optional
from src.common.logging import info, error, success, debug
import questionary


# List of common editors to check for availability
COMMON_EDITORS = [
    "nano", "vim", "nvim", "vi", "micro", "code", "subl", "gedit", "mate"
]

# Usage guides for CLI editors
EDITOR_GUIDES: Dict[str, Dict[str, str]] = {
    "nano": {
        "Edit content": "Type directly in the content area",
        "Delete content": "Use Delete or Backspace keys",
        "Search": "Ctrl + W",
        "Save and exit": "Ctrl + O → Enter, then Ctrl + X",
        "Exit without saving": "Ctrl + X, then select N"
    },
    "vim": {
        "Edit content": "Press i to enter INSERT mode",
        "Delete content": "In INSERT mode, use Delete or Backspace",
        "Search": "/ + keyword, press Enter",
        "Save and exit": ":wq + Enter",
        "Exit without saving": ":q! + Enter"
    },
    "micro": {
        "Edit content": "Type directly in the content area",
        "Delete content": "Use Delete or Backspace keys",
        "Search": "Ctrl + F",
        "Save and exit": "Ctrl + S then Ctrl + Q",
        "Exit without saving": "Ctrl + Q then choose not to save"
    },
    "vi": {
        "Edit content": "Press i to enter INSERT mode",
        "Delete content": "In INSERT mode, use Delete or Backspace",
        "Search": "/ + keyword, press Enter",
        "Save and exit": ":wq + Enter",
        "Exit without saving": ":q! + Enter"
    }
    # GUI editors like code, subl, gedit don't need CLI guides
}


def choose_editor(default: Optional[str] = None) -> Optional[str]:
    """
    Display a list of available editors and let the user choose one.
    
    If default is provided and available, it will be pre-selected.
    After selection, displays usage guide and asks for confirmation.
    
    Args:
        default: Default editor to pre-select
        
    Returns:
        Selected editor command or None if cancelled
    """
    available_editors = [editor for editor in COMMON_EDITORS if shutil.which(editor)]

    if not available_editors:
        error("❌ No text editors found on the system.")
        return None

    default_choice = default if default in available_editors else available_editors[0]

    selected = questionary.select(
        "Choose a text editor:",
        choices=available_editors,
        default=default_choice
    ).ask()

    if selected in EDITOR_GUIDES:
        guide = EDITOR_GUIDES[selected]
        info("\n📘 Editor usage guide:")
        for key, val in guide.items():
            info(f"- {key}: {val}")

    confirm = questionary.confirm("Do you want to continue with this editor?").ask()
    if not confirm:
        error("❌ Editor opening cancelled.")
        return None

    return selected


def get_available_editors() -> List[str]:
    """
    Get a list of available text editors on the system.
    
    Returns:
        List of available editor commands
    """
    return [editor for editor in COMMON_EDITORS if shutil.which(editor)]
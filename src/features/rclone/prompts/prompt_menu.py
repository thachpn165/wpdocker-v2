"""
Rclone management menu prompt module.

This module provides the user interface for Rclone management functions.
"""

import questionary
from questionary import Style
from typing import Optional

from src.common.logging import info, error, debug, success

def not_implemented() -> None:
    """Handle not implemented features."""
    error("🚧 Feature not implemented yet")
    input("Press Enter to continue...")

# Custom style for the menu
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:cyan bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:green bold'),
    ('selected', 'fg:green bold'),
    ('separator', 'fg:cyan'),
    ('instruction', 'fg:gray'),
    ('text', ''),
    ('disabled', 'fg:gray italic'),
])

def prompt_rclone_menu() -> None:
    """Display Rclone management menu and handle user selection."""
    try:
        try:
            # Try to import the original Rclone prompt function
            from src.features.rclone.prompts.rclone_prompt import prompt_rclone_menu as original_prompt
            original_prompt()
            return
        except ImportError:
            choices = [
                {"name": "1. Manage RClone", "value": "1"},
                {"name": "0. Back to Main Menu", "value": "0"},
            ]
            
            answer = questionary.select(
                "\n📦 RClone Management:",
                choices=choices,
                style=custom_style
            ).ask()
            
            if answer != "0":
                not_implemented()
    except Exception as e:
        error(f"Error in cloud menu: {e}")
        input("Press Enter to continue...")
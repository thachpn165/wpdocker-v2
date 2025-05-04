"""
Cron job management menu prompt module.

This module provides the user interface for cron job management functions
like listing, enabling/disabling, and deleting tasks.
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

def prompt_cron_menu() -> None:
    """Display cron job management menu and handle user selection."""
    try:
        choices = [
            {"name": "1. List Tasks", "value": "1"},
            {"name": "2. Enable/Disable Task", "value": "2"},
            {"name": "3. Delete Task", "value": "3"},
            {"name": "4. Run Task Now", "value": "4"},
            {"name": "0. Back to System Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n⏱️ Scheduled Task Management:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer != "0":
            not_implemented()
    except Exception as e:
        error(f"Error in cron menu: {e}")
        input("Press Enter to continue...")
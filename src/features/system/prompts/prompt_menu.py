"""
System tools menu prompt module.

This module provides the user interface for system management functions
like rebuilding containers, updating versions, and viewing system information.
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

def prompt_system_menu() -> None:
    """Display system tools menu and handle user selection."""
    try:
        choices = [
            {"name": "1. Rebuild Core Containers", "value": "1"},
            {"name": "2. Update WP Docker Version", "value": "2"},
            {"name": "3. View System Information", "value": "3"},
            {"name": "4. Change Language", "value": "4"},
            {"name": "5. Change Version Channel", "value": "5"},
            {"name": "6. Clean Docker", "value": "6"},
            {"name": "7. Manage Scheduled Tasks", "value": "7"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n⚙️ System Tools:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "7":
            from src.features.cron.prompts.prompt_menu import prompt_cron_menu
            prompt_cron_menu()
        elif answer != "0":
            not_implemented()
    except Exception as e:
        error(f"Error in system menu: {e}")
        input("Press Enter to continue...")
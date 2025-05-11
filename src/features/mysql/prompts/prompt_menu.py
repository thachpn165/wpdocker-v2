"""
MySQL management menu prompt module.

This module provides the user interface for MySQL management functions
like editing MySQL configuration and restoring databases.
"""

import questionary
from questionary import Style
from typing import Optional

from src.common.logging import info, error, debug, success
from src.common.ui.menu_utils import with_pause, pause_after_action

# Import prompts
from src.features.mysql.prompts.prompt_config_editor import prompt_mysql_config
from src.features.mysql.prompts.prompt_restore import prompt_restore_database


@with_pause
def not_implemented() -> None:
    """Handle not implemented features."""
    error("🚧 Feature not implemented yet")


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


def prompt_mysql_menu() -> None:
    """Display MySQL management menu and handle user selection."""
    try:
        choices = [
            {"name": "1. Edit MySQL Configuration", "value": "1"},
            {"name": "2. Restore Database", "value": "2"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]

        answer = questionary.select(
            "\n🗄️ MySQL Management:",
            choices=choices,
            style=custom_style
        ).ask()

        if answer == "1":
            prompt_mysql_config()
        elif answer == "2":
            prompt_restore_database()
        # answer "0" just returns to main menu
    except Exception as e:
        error(f"Error in MySQL menu: {e}")
        input("Press Enter to continue...")

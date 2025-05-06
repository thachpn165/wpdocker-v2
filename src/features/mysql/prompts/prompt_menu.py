"""
MySQL management menu prompt module.

This module provides the user interface for MySQL management functions
like editing MySQL configuration and restoring databases.
"""

import questionary
from questionary import Style
from typing import Optional
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.common.logging import info, error, debug, success, log_call

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

@log_call
@with_pause
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
            try:
                from src.features.mysql.cli.config_editor import cli_mysql_config
                cli_mysql_config()
                pause_after_action()
            except ImportError:
                not_implemented()
        elif answer == "2":
            try:
                from src.features.mysql.cli.restore import cli_restore_database
                cli_restore_database()
                pause_after_action()
            except ImportError:
                not_implemented()
        # answer "0" just returns to main menu
    except Exception as e:
        error(f"Error in MySQL menu: {e}")
        input("Press Enter to continue...")

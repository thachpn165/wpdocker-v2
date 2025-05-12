"""
WordPress auto-update prompt module.

This module provides the user interface for managing WordPress auto-update settings,
including enabling/disabling auto-updates for themes and plugins.
"""

import questionary
from questionary import Style
from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.website.utils import select_website
from src.features.wordpress.cli.auto_update import (
    cli_toggle_theme_auto_update,
    cli_toggle_plugin_auto_update
)


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


@with_pause
def prompt_auto_update_menu() -> None:
    """
    Display WordPress auto-update menu and handle user selection.
    
    This function displays a user-friendly menu for managing WordPress auto-update settings,
    calling the appropriate CLI implementations based on user selection.
    """
    try:
        choices = [
            {"name": "1. Toggle Auto Update Theme", "value": "theme"},
            {"name": "2. Toggle Auto Update Plugin", "value": "plugin"},
            {"name": "0. Back", "value": "0"},
        ]
        answer = questionary.select(
            "\n⚡ Auto Update Options:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "0":
            return
            
        domain = select_website("Chọn website cần thao tác auto update:")
        if not domain:
            info("Không có website nào hoặc thao tác bị hủy. Quay lại menu.")
            return
            
        if answer == "theme":
            cli_toggle_theme_auto_update(domain, interactive=True)
        elif answer == "plugin":
            cli_toggle_plugin_auto_update(domain, interactive=True)
            
        # Pause after action is handled by the decorator
        return True
    except Exception as e:
        error(f"Error in auto-update menu: {e}")
        input("Press Enter to continue...")
        return False
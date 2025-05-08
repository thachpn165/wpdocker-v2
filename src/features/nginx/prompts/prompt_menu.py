"""
NGINX management menu prompt module.

This module provides the user interface for NGINX management functions
like testing configuration, reloading, restarting, and managing caches.
"""

import questionary
from questionary import Style
from typing import Optional

from src.common.logging import info, error, debug, success
from src.common.ui.menu_utils import with_pause, pause_after_action

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
def not_implemented() -> None:
    """Handle not implemented features."""
    error("🚧 Feature not implemented yet")

def prompt_nginx_menu() -> None:
    """Display NGINX management menu and handle user selection."""
    try:
        choices = [
            {"name": "1. Test Configuration", "value": "1"},
            {"name": "2. Reload Configuration", "value": "2"},
            {"name": "3. Restart NGINX Container", "value": "3"},
            {"name": "4. Manage Cache", "value": "4"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n🌐 NGINX Management:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "1":
            try:
                from src.features.nginx.prompts.prompt_test_config import prompt_test_config
                prompt_test_config()
            except ImportError:
                from src.features.nginx.cli.config import cli_test_config
                cli_test_config()
                pause_after_action()
        elif answer == "2":
            try:
                from src.features.nginx.prompts.prompt_reload import prompt_reload
                prompt_reload()
            except ImportError:
                from src.features.nginx.cli.reload import cli_reload
                cli_reload()
                pause_after_action()
        elif answer == "3":
            try:
                from src.features.nginx.prompts.prompt_restart import prompt_restart
                prompt_restart()
            except ImportError:
                from src.features.nginx.cli.restart import cli_restart
                cli_restart()
                pause_after_action()
        elif answer == "4":
            try:
                from src.features.nginx.prompts.prompt_cache import prompt_manage_cache
                prompt_manage_cache()
            except ImportError:
                from src.features.nginx.cli.cache import cli_manage_cache
                cli_manage_cache()
                pause_after_action()
        # answer "0" just returns to main menu
    except Exception as e:
        error(f"Error in NGINX menu: {e}")
        input("Press Enter to continue...")
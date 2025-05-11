"""
PHP management menu prompt module.

This module provides the user interface for PHP management functions
like changing PHP version, editing PHP configuration, and installing extensions.
"""

import questionary
from questionary import Style
from typing import Optional, Callable, Any

from src.common.logging import info, error, debug, success
from src.common.ui.menu_utils import with_pause, pause_after_action

# Import prompts
from src.features.php.prompts.prompt_version import prompt_change_php_version
from src.features.php.prompts.prompt_config_editor import prompt_edit_php_config
from src.features.php.prompts.prompt_extensions import prompt_php_extensions_menu, prompt_list_extensions, prompt_install_extension, prompt_uninstall_extension


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


def prompt_php_menu() -> None:
    """Display PHP management menu and handle user selection."""
    try:
        choices = [
            {"name": "1. Change PHP Version", "value": "1"},
            {"name": "2. Edit PHP Configuration", "value": "2"},
            {"name": "3. Manage PHP Extensions", "value": "3"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]

        answer = questionary.select(
            "\n🐘 PHP Management:",
            choices=choices,
            style=custom_style
        ).ask()

        if answer == "1":
            prompt_change_php_version()
        elif answer == "2":
            prompt_edit_php_config()
        elif answer == "3":
            prompt_php_extensions_menu()
        # answer "0" just returns to main menu
    except Exception as e:
        error(f"Error in PHP menu: {e}")
        input("Press Enter to continue...")
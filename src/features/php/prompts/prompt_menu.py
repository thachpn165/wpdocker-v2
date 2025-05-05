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
            try:
                from src.features.php.cli.version import cli_change_php_version
                cli_change_php_version()
                pause_after_action()
            except ImportError:
                not_implemented()
        elif answer == "2":
            try:
                from src.features.php.cli.config_editor import cli_edit_php_config
                cli_edit_php_config()
                pause_after_action()
            except ImportError:
                not_implemented()
        elif answer == "3":
            prompt_php_extensions_menu()
        # answer "0" just returns to main menu
    except Exception as e:
        error(f"Error in PHP menu: {e}")
        input("Press Enter to continue...")

def prompt_php_extensions_menu() -> None:
    """Display PHP extensions management submenu."""
    try:
        choices = [
            {"name": "1. List Extensions", "value": "1"},
            {"name": "2. Install Extension", "value": "2"},
            {"name": "3. Uninstall Extension", "value": "3"},
            {"name": "0. Back to PHP Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n🔌 PHP Extensions Management:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "1":
            try:
                from src.features.php.cli.extensions import cli_list_extensions
                cli_list_extensions()
                pause_after_action()
            except ImportError:
                not_implemented()
        elif answer == "2":
            try:
                from src.features.php.cli.extensions import cli_install_extension
                cli_install_extension()
                pause_after_action()
            except ImportError:
                not_implemented()
        elif answer == "3":
            try:
                from src.features.php.cli.extensions import cli_uninstall_extension
                cli_uninstall_extension()
                pause_after_action()
            except ImportError:
                not_implemented()
        elif answer == "0":
            # Return to PHP menu
            prompt_php_menu()
    except Exception as e:
        error(f"Error in PHP extensions menu: {e}")
        input("Press Enter to continue...")
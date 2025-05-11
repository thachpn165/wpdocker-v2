"""
PHP extensions management prompt module.

This module provides the user interface for managing PHP extensions,
including listing, installing, and uninstalling extensions.
"""

import questionary
from questionary import Style
from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.php.cli.extensions import cli_list_extensions, cli_install_extension, cli_uninstall_extension


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
def prompt_list_extensions() -> None:
    """
    Display PHP extensions listing prompt and handle the listing process.
    
    This function calls the CLI implementation to list PHP extensions.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_list_extensions()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in PHP extensions listing prompt: {e}")
        input("Press Enter to continue...")
        return False


@with_pause
def prompt_install_extension() -> None:
    """
    Display PHP extension installation prompt and handle the installation process.
    
    This function calls the CLI implementation to install a PHP extension.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_install_extension()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in PHP extension installation prompt: {e}")
        input("Press Enter to continue...")
        return False


@with_pause
def prompt_uninstall_extension() -> None:
    """
    Display PHP extension uninstallation prompt and handle the uninstallation process.
    
    This function calls the CLI implementation to uninstall a PHP extension.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_uninstall_extension()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in PHP extension uninstallation prompt: {e}")
        input("Press Enter to continue...")
        return False


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
            prompt_list_extensions()
        elif answer == "2":
            prompt_install_extension()
        elif answer == "3":
            prompt_uninstall_extension()
        # answer "0" just returns to PHP menu
    except Exception as e:
        error(f"Error in PHP extensions menu: {e}")
        input("Press Enter to continue...")
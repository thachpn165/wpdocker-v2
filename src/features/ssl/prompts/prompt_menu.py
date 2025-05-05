"""
SSL certificate management menu prompt module.

This module provides the user interface for SSL certificate management functions
like creating, installing, and checking certificates.
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

def prompt_ssl_menu() -> None:
    """Display SSL certificate management menu and handle user selection."""
    try:
        choices = [
            {"name": "1. Install SSL Certificate", "value": "1"},
            {"name": "2. Check Certificate Info", "value": "2"},
            {"name": "3. Edit Current Certificate", "value": "3"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n🔒 SSL Certificate Management:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "1":
            try:
                from src.features.ssl.cli.install import cli_install_ssl
                cli_install_ssl()
                pause_after_action()
            except ImportError:
                not_implemented()
        elif answer == "2":
            try:
                from src.features.ssl.cli.check import cli_check_ssl
                cli_check_ssl()
                pause_after_action()
            except ImportError:
                not_implemented()
        elif answer == "3":
            try:
                from src.features.ssl.cli.edit import cli_edit_ssl
                cli_edit_ssl()
                pause_after_action()
            except ImportError:
                not_implemented()
        # answer "0" just returns to main menu
    except Exception as e:
        error(f"Error in SSL menu: {e}")
        input("Press Enter to continue...")
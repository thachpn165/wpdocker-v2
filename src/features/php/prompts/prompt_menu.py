"""
PHP management menu prompt module.

This module provides the user interface for PHP management functions
like changing PHP version, editing PHP configuration, and installing extensions.
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

def prompt_php_menu() -> None:
    """Display PHP management menu and handle user selection."""
    choices = [
        {"name": "1. Change PHP Version", "value": "1"},
        {"name": "2. Edit PHP Configuration", "value": "2"},
        {"name": "3. Install PHP Extension", "value": "3"},
        {"name": "0. Back to Main Menu", "value": "0"},
    ]
    
    answer = questionary.select(
        "\n🐘 PHP Management:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if answer != "0":
        not_implemented()
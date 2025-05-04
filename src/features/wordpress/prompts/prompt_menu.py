"""
WordPress tools menu prompt module.

This module provides the user interface for WordPress management functions
like installing WordPress, managing plugins and themes.
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

def prompt_wordpress_menu() -> None:
    """Display WordPress tools menu and handle user selection."""
    choices = [
        {"name": "1. Install WordPress", "value": "1"},
        {"name": "2. Manage Plugins", "value": "2"},
        {"name": "3. Manage Themes", "value": "3"},
        {"name": "4. Change WordPress Settings", "value": "4"},
        {"name": "0. Back to Main Menu", "value": "0"},
    ]
    
    answer = questionary.select(
        "\n🔌 WordPress Tools:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if answer != "0":
        not_implemented()
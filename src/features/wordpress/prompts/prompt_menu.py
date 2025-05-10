"""
WordPress tools menu prompt module.

This module provides the user interface for WordPress management functions
like installing WordPress, managing plugins and themes.
"""

import questionary
from questionary import Style
from typing import Optional

from src.common.logging import info, error, debug, success
from src.features.website.utils import select_website
from src.features.wordpress.cli.auto_update import (
    cli_toggle_theme_auto_update,
    cli_toggle_plugin_auto_update,
)

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

def prompt_auto_update_menu() -> None:
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

def prompt_wordpress_menu() -> None:
    """Display WordPress tools menu and handle user selection."""
    choices = [
        {"name": "1. Toggle Auto Update", "value": "auto_update"},
        {"name": "2. Toggle wp-login.php Protection", "value": "wp_login_protect"},
        {"name": "3. Reset Admin Password", "value": "reset_admin_pw"},
        {"name": "4. Reset User Role", "value": "reset_user_role"},
        {"name": "0. Back to Main Menu", "value": "0"},
    ]
    answer = questionary.select(
        "\n🔌 WordPress Tools:",
        choices=choices,
        style=custom_style
    ).ask()
    if answer == "auto_update":
        prompt_auto_update_menu()
    elif answer != "0":
        not_implemented()
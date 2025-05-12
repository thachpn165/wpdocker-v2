"""
WordPress tools menu prompt module.

This module provides the user interface for WordPress management functions
like installing WordPress, managing plugins and themes.
"""

import questionary
from questionary import Style
from typing import Optional

from src.common.logging import info, error, debug, success
from src.common.ui.menu_utils import with_pause

# Import prompts
from src.features.wordpress.prompts.prompt_auto_update import prompt_auto_update_menu
from src.features.wordpress.prompts.prompt_protect import prompt_toggle_wp_login_protection
from src.features.wordpress.prompts.prompt_user import prompt_reset_admin_password, prompt_reset_user_role
from src.features.wordpress.prompts.prompt_install import prompt_install_wordpress
from src.features.wordpress.prompts.prompt_manage import prompt_run_wp_command, prompt_uninstall_wordpress


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


def prompt_wordpress_menu() -> None:
    """Display WordPress tools menu and handle user selection."""
    choices = [
        {"name": "1. Install WordPress", "value": "install"},
        {"name": "2. Run WP-CLI Command", "value": "wp_command"},
        {"name": "3. Uninstall WordPress", "value": "uninstall"},
        {"name": "4. Toggle Auto Update", "value": "auto_update"},
        {"name": "5. Toggle wp-login.php Protection", "value": "wp_login_protect"},
        {"name": "6. Reset Admin Password", "value": "reset_admin_pw"},
        {"name": "7. Reset User Role", "value": "reset_user_role"},
        {"name": "0. Back to Main Menu", "value": "0"},
    ]
    answer = questionary.select(
        "\n🔌 WordPress Tools:",
        choices=choices,
        style=custom_style
    ).ask()

    if answer == "install":
        prompt_install_wordpress()
    elif answer == "wp_command":
        prompt_run_wp_command()
    elif answer == "uninstall":
        prompt_uninstall_wordpress()
    elif answer == "auto_update":
        prompt_auto_update_menu()
    elif answer == "wp_login_protect":
        prompt_toggle_wp_login_protection()
    elif answer == "reset_admin_pw":
        prompt_reset_admin_password()
    elif answer == "reset_user_role":
        prompt_reset_user_role()
    elif answer != "0":
        not_implemented()

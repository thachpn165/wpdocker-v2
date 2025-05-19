"""
WordPress protection prompt module.

This module provides the user interface for managing WordPress protection settings,
including securing the wp-login.php page.
"""

from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.website.utils import select_website
from src.features.wordpress.cli.protect import cli_toggle_wp_login_protection


@with_pause
def prompt_toggle_wp_login_protection() -> None:
    """
    Display wp-login.php protection toggle prompt and handle the protection change.
    
    This function displays a user-friendly menu for toggling wp-login.php protection,
    calling the CLI implementation to perform the actual change.
    """
    try:
        domain = select_website("Select website to change wp-login.php protection:")
        if not domain:
            info("No website found or operation cancelled. Returning to menu.")
            return False
            
        result = cli_toggle_wp_login_protection(domain, interactive=True)
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in wp-login.php protection toggle prompt: {e}")
        input("Press Enter to continue...")
        return False
"""
WordPress installation prompt module.

This module provides the user interface for installing WordPress on a website,
handling user interaction for installation parameters.
"""

from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.wordpress.cli.install import cli_install_wordpress


@with_pause
def prompt_install_wordpress(domain: Optional[str] = None) -> None:
    """
    Display WordPress installation prompt and handle the installation process.
    
    Args:
        domain: Optional domain name. If provided, skips the website selection step.
    
    This function displays a user-friendly menu for installing WordPress,
    calling the CLI implementation to perform the actual installation.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_install_wordpress(domain)
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in WordPress installation prompt: {e}")
        input("Press Enter to continue...")
        return False
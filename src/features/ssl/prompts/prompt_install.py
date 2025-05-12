"""
SSL installation prompt module.

This module provides the user interface for installing SSL certificates,
handling user interaction for certificate type selection and parameter input.
"""

from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.ssl.cli.install import cli_install_ssl


@with_pause
def prompt_install_ssl() -> None:
    """
    Display SSL certificate installation prompt and handle the installation process.
    
    This function displays a user-friendly menu for installing SSL certificates,
    calling the CLI implementation to perform the actual installation.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_install_ssl()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in SSL certificate installation prompt: {e}")
        input("Press Enter to continue...")
        return False
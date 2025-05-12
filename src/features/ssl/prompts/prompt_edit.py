"""
SSL editor prompt module.

This module provides the user interface for editing SSL certificates,
handling user interaction for backup and restore operations.
"""

from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.ssl.cli.edit import cli_edit_ssl


@with_pause
def prompt_edit_ssl() -> None:
    """
    Display SSL certificate edit prompt and handle the certificate editing process.
    
    This function displays a user-friendly menu for editing SSL certificates,
    calling the CLI implementation to perform the actual edit.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_edit_ssl()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in SSL certificate edit prompt: {e}")
        input("Press Enter to continue...")
        return False
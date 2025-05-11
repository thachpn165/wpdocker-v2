"""
MySQL database restore prompt module.

This module provides the user interface for restoring MySQL databases,
handling user interaction for selecting databases and backup files.
"""

from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.mysql.cli.restore import cli_restore_database


@with_pause
def prompt_restore_database() -> None:
    """
    Display database restore prompt and handle the restoration process.
    
    This function displays a user-friendly menu for restoring MySQL databases,
    calling the CLI implementation to perform the actual restoration.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_restore_database()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in database restore prompt: {e}")
        input("Press Enter to continue...")
        return False
"""
Website restart prompt module.

This module provides the user interface for restarting websites,
handling user selection and confirmation.
"""

from questionary import confirm
from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.website.cli.restart import cli_restart_website


@with_pause
def prompt_restart_website() -> None:
    """
    Display website restart prompt and handle the restart process.
    
    This function displays a user-friendly menu for restarting a website,
    calling the CLI implementation to perform the actual restart.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_restart_website()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in website restart prompt: {e}")
        input("Press Enter to continue...")
        return False
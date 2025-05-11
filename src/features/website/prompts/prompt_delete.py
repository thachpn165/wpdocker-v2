"""
Website deletion prompt module.

This module provides the user interface for deleting websites,
handling user confirmation and parameter validation.
"""

import questionary
from questionary import confirm
from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.website.cli.delete import cli_delete_website


@with_pause
def prompt_delete_website() -> None:
    """
    Display website deletion prompt and handle the deletion process.
    
    This function displays a user-friendly menu for deleting a website,
    calling the CLI implementation to perform the actual deletion.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_delete_website()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in website deletion prompt: {e}")
        input("Press Enter to continue...")
        return False
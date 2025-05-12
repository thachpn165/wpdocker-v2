"""
Website listing prompt module.

This module provides the user interface for listing websites.
"""

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.website.cli.list import cli_list_websites


@with_pause
def prompt_list_websites() -> None:
    """
    Display website listing prompt and handle the listing process.
    
    This function displays a user-friendly menu for listing websites,
    calling the CLI implementation to perform the actual listing.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        # Set json=False to show formatted output for interactive mode
        result = cli_list_websites(json=False)
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in website listing prompt: {e}")
        input("Press Enter to continue...")
        return False
"""
Website info prompt module.

This module provides the user interface for viewing website information.
"""

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.website.cli.info import cli_website_info


@with_pause
def prompt_website_info() -> None:
    """
    Display website info prompt and handle the information display.
    
    This function displays a user-friendly menu for viewing website information,
    calling the CLI implementation to perform the actual information retrieval.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        # Set json=False to show formatted output for interactive mode
        result = cli_website_info(json=False)
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in website info prompt: {e}")
        input("Press Enter to continue...")
        return False
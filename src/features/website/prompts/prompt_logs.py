"""
Website logs prompt module.

This module provides the user interface for viewing website logs.
"""

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.website.cli.logs import cli_view_logs


@with_pause
def prompt_view_logs() -> None:
    """
    Display website logs prompt and handle the log viewing process.
    
    This function displays a user-friendly menu for viewing website logs,
    calling the CLI implementation to perform the actual log retrieval.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_view_logs()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in website logs prompt: {e}")
        input("Press Enter to continue...")
        return False
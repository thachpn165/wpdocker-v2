"""
SSL checker prompt module.

This module provides the user interface for checking SSL certificates,
displaying certificate information in a user-friendly format.
"""

from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.ssl.cli.check import cli_check_ssl


@with_pause
def prompt_check_ssl() -> None:
    """
    Display SSL certificate check prompt and handle the certificate checking process.
    
    This function displays a user-friendly menu for checking SSL certificates,
    calling the CLI implementation to perform the actual check.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        # Set json_output=False for better human-readable output
        result = cli_check_ssl(json_output=False)
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in SSL certificate check prompt: {e}")
        input("Press Enter to continue...")
        return False
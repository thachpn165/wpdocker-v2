"""
PHP version management prompt module.

This module provides the user interface for changing PHP versions,
handling user interaction for version selection.
"""

from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.php.cli.version import cli_change_php_version


@with_pause
def prompt_change_php_version() -> None:
    """
    Display PHP version change prompt and handle the version change process.
    
    This function displays a user-friendly menu for changing PHP versions,
    calling the CLI implementation to perform the actual version change.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_change_php_version()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in PHP version change prompt: {e}")
        input("Press Enter to continue...")
        return False
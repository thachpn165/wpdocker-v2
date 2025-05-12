"""
PHP configuration editor prompt module.

This module provides the user interface for editing PHP configuration files,
handling user interaction for file selection and editor operations.
"""

from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.php.cli.config_editor import cli_edit_php_config


@with_pause
def prompt_edit_php_config() -> None:
    """
    Display PHP configuration editor prompt and handle the editing process.
    
    This function displays a user-friendly menu for editing PHP configuration files,
    calling the CLI implementation to perform the actual editing.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_edit_php_config()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in PHP configuration editor prompt: {e}")
        input("Press Enter to continue...")
        return False
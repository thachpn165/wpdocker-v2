"""
MySQL configuration editor prompt module.

This module provides the user interface for editing MySQL configuration,
handling user interaction for configuration management operations.
"""

from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.mysql.cli.config_editor import cli_mysql_config


@with_pause
def prompt_mysql_config() -> None:
    """
    Display MySQL configuration editor prompt and handle the configuration management process.
    
    This function displays a user-friendly menu for managing MySQL configuration,
    calling the CLI implementation to perform the actual operations.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_mysql_config()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in MySQL configuration editor prompt: {e}")
        input("Press Enter to continue...")
        return False
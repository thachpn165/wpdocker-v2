"""
WordPress management prompt module.

This module provides the user interface for managing WordPress installations,
including running WP-CLI commands and performing administrative tasks.
"""

from typing import Optional

from src.common.logging import info, warn, error, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.wordpress.cli.manage import cli_run_wp_command, cli_uninstall_wordpress


@with_pause
def prompt_run_wp_command() -> None:
    """
    Display WP-CLI command prompt and handle the command execution.
    
    This function displays a user-friendly menu for running WP-CLI commands,
    calling the CLI implementation to perform the actual command execution.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_run_wp_command()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in WP-CLI command prompt: {e}")
        input("Press Enter to continue...")
        return False


@with_pause
def prompt_uninstall_wordpress() -> None:
    """
    Display WordPress uninstallation prompt and handle the uninstallation process.
    
    This function displays a user-friendly menu for uninstalling WordPress,
    calling the CLI implementation to perform the actual uninstallation.
    """
    try:
        # Call the CLI function which handles all the interactive prompts
        result = cli_uninstall_wordpress()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in WordPress uninstallation prompt: {e}")
        input("Press Enter to continue...")
        return False
"""
NGINX reload prompt module.

This module provides the user interface for reloading NGINX configuration.
"""

import questionary
from typing import Optional

from src.common.logging import info, error, debug, success
from src.common.ui.menu_utils import pause_after_action

def prompt_reload() -> None:
    """Prompt for reloading NGINX configuration."""
    try:
        # Ask for confirmation before reloading
        confirm = questionary.confirm(
            "Are you sure you want to reload NGINX configuration?",
            default=True
        ).ask()
        
        if not confirm:
            info("Operation cancelled.")
            input("Press Enter to continue...")
            return
            
        # Call the CLI function with interactive mode
        from src.features.nginx.cli.reload import cli_reload
        cli_reload(interactive=True)
        
        # Pause to let the user read the output
        pause_after_action()
    except Exception as e:
        error(f"Error reloading NGINX configuration: {e}")
        input("Press Enter to continue...")
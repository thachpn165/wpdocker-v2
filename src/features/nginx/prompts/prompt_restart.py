"""
NGINX restart prompt module.

This module provides the user interface for restarting the NGINX container.
"""

import questionary
from typing import Optional

from src.common.logging import info, error, debug, success, warn
from src.common.ui.menu_utils import pause_after_action

def prompt_restart() -> None:
    """Prompt for restarting NGINX container."""
    try:
        # Show warning and ask for confirmation
        warn("⚠️ Restarting NGINX will temporarily disconnect all active websites.")
        warn("⚠️ This operation may cause a brief service interruption.")
        
        confirm = questionary.confirm(
            "Are you sure you want to restart the NGINX container?",
            default=False
        ).ask()
        
        if not confirm:
            info("Operation cancelled.")
            input("Press Enter to continue...")
            return
            
        # Call the CLI function with interactive mode
        from src.features.nginx.cli.restart import cli_restart
        cli_restart(interactive=True)
        
        # Pause to let the user read the output
        pause_after_action()
    except Exception as e:
        error(f"Error restarting NGINX container: {e}")
        input("Press Enter to continue...")
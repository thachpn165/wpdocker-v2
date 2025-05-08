"""
NGINX test configuration prompt module.

This module provides the user interface for testing NGINX configuration.
"""

from src.common.logging import info, error, debug, success
from src.common.ui.menu_utils import pause_after_action

def prompt_test_config() -> None:
    """Prompt for testing NGINX configuration."""
    try:
        from src.features.nginx.cli.config import cli_test_config
        
        # Call the CLI function with interactive mode
        cli_test_config(interactive=True)
        
        # Pause to let the user read the output
        pause_after_action()
    except Exception as e:
        error(f"Error testing NGINX configuration: {e}")
        input("Press Enter to continue...")
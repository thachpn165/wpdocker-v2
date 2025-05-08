"""
NGINX cache management prompt module.

This module provides the user interface for managing NGINX cache configuration.
"""

import questionary
from typing import Optional, List

from src.common.logging import info, error, debug, success
from src.common.ui.menu_utils import pause_after_action
from src.features.nginx.utils.config_utils import get_available_cache_configs

def prompt_manage_cache() -> None:
    """Prompt for managing NGINX cache configuration."""
    try:
        # Call the CLI function to handle cache management
        # The CLI function already has interactive mode handling
        from src.features.nginx.cli.cache import cli_manage_cache
        cli_manage_cache(interactive=True)
        
        # Pause to let the user read the output is handled within the CLI function
    except Exception as e:
        error(f"Error managing NGINX cache: {e}")
        input("Press Enter to continue...")
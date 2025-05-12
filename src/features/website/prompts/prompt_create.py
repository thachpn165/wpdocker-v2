"""
Website creation prompt module.

This module provides the user interface for creating new websites,
handling user input validation and parameter collection.
"""

import questionary
from questionary import text, select, confirm
from typing import Optional, Dict, Any

from src.common.logging import info, warn, error, success, log_call
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.website.cli.create import cli_create_website
from src.common.utils.validation import is_valid_domain
from src.features.website.utils import is_website_exists


@with_pause
def prompt_create_website() -> None:
    """
    Display website creation prompt and handle the creation process.
    
    This function displays a user-friendly menu for creating a new website,
    calling the CLI implementation to perform the actual creation.
    """
    try:
        # Call the CLI function with interactive mode
        result = cli_create_website()
        
        # Pause after action is handled by the decorator
        return result
    except Exception as e:
        error(f"Error in website creation prompt: {e}")
        input("Press Enter to continue...")
        return False
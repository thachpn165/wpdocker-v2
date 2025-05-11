"""
Language change prompt module.

This module provides the user interface for changing the system language.
"""

import questionary
from questionary import Style
from typing import Optional

from src.common.logging import info, error, debug, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.features.system.cli.change_language import cli_change_language


@with_pause
def prompt_change_language() -> None:
    """
    Display language selection prompt and handle the change.
    
    This function displays a user-friendly menu for changing the system language,
    calling the CLI implementation to perform the actual change.
    """
    try:
        # The interactive flag is true because it's being called from the menu
        # This will auto-show the questionary selection
        result = cli_change_language(interactive=True)

        
        return result
    except Exception as e:
        error(f"Error in language change prompt: {e}")
        input("Press Enter to continue...")
        return False
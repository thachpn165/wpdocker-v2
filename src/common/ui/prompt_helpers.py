"""
Prompt and UI helper functions.

This module provides common UI and prompt-related functionality used throughout the application.
"""

import questionary
from questionary import Style
from typing import Dict, List, Optional, Any, Callable

from src.common.logging import info, error, debug

# Custom style for the menu
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:cyan bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:green bold'),
    ('selected', 'fg:green bold'),
    ('separator', 'fg:cyan'),
    ('instruction', 'fg:gray'),
    ('text', ''),
    ('disabled', 'fg:gray italic'),
])


def wait_for_enter(error_occurred: bool = False) -> None:
    """
    Display a prompt for the user to press Enter to continue.
    
    Args:
        error_occurred: Whether an error occurred, affecting formatting
    """
    if error_occurred:
        input("Press Enter to continue...")
    else:
        input("\nPress Enter to continue...")


def create_menu_choices(items: List[Dict], include_back: bool = True) -> List[Dict]:
    """
    Create a standardized list of choices for menu display.
    
    Args:
        items: List of menu items with name and value keys
        include_back: Whether to include a "Back" option
        
    Returns:
        Formatted list of choices
    """
    choices = []
    
    for i, item in enumerate(items, 1):
        if isinstance(item, dict) and "name" in item and "value" in item:
            choices.append({"name": f"{i}. {item['name']}", "value": item["value"]})
        else:
            choices.append({"name": f"{i}. {item}", "value": str(i)})
    
    if include_back:
        choices.append({"name": "0. Back", "value": "0"})
        
    return choices


def prompt_with_cancel(choices: List[Dict], message: str) -> Optional[str]:
    """
    Display a selection prompt with Cancel option, handling the cancel case.
    
    Args:
        choices: List of choices for questionary select
        message: Prompt message to display
        
    Returns:
        Selected value or None if cancelled
    """
    selected = questionary.select(
        message,
        choices=choices,
        style=custom_style
    ).ask()
    
    if selected == "cancel":
        return None
    
    return selected


def execute_with_exception_handling(func: Callable, error_message: str) -> None:
    """
    Execute a function with standardized exception handling.
    
    Args:
        func: Function to execute
        error_message: Error message prefix to show on exception
    """
    try:
        func()
    except Exception as e:
        error(f"{error_message}: {e}")
        wait_for_enter(True)
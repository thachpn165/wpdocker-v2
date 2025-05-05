"""
Prompt helper functions.

This module provides helper functions to create consistent and reusable
user interface components for all prompts in the application.
"""

import functools
from typing import Callable, Any, TypeVar, List, Dict, Optional, cast

import questionary
from questionary import Style

from src.common.logging import info, error, debug
from src.common.ui.menu_utils import pause_after_action, with_pause

# Reusable prompt style
PROMPT_STYLE = Style([
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

F = TypeVar('F', bound=Callable[..., Any])

def create_menu_handler(import_path: str, function_name: str) -> Callable[[], None]:
    """
    Create a menu handler function that imports and calls another function.
    
    This simplifies creating menu items that need to import functionality
    from other modules.
    
    Args:
        import_path: Path to the module to import
        function_name: Name of the function to call
    
    Returns:
        A handler function that imports and calls the specified function
    """
    @with_pause
    def handler() -> None:
        try:
            module = __import__(import_path, fromlist=[function_name])
            func = getattr(module, function_name)
            func()
        except ImportError:
            error(f"🚧 Feature '{function_name}' not implemented yet")
        except Exception as e:
            error(f"Error executing {function_name}: {e}")
    
    return handler

def create_prompt_menu(
    title: str,
    options: List[Dict[str, Any]],
    back_option: bool = True
) -> str:
    """
    Create a consistent prompt menu with options.
    
    Args:
        title: Title of the menu
        options: List of option dictionaries with 'name', 'value', and optionally 'disabled'
        back_option: Whether to add a "Back" option (defaults to True)
    
    Returns:
        Selected option value
    """
    if back_option:
        options.append({"name": "0. Back", "value": "0"})
    
    try:
        return questionary.select(
            title,
            choices=options,
            style=PROMPT_STYLE
        ).ask() or "0"  # Default to "0" if None (e.g., user pressed Ctrl+C)
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return "0"
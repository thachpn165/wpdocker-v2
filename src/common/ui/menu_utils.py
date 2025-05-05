"""
Menu utility functions.

This module provides common menu-related functionality used throughout the application.
"""

import functools
from typing import Callable, Any, TypeVar, cast

from src.common.logging import debug

# Define a generic type for functions
F = TypeVar('F', bound=Callable[..., Any])

def with_pause(func: F) -> F:
    """
    Decorator that adds a pause (Press Enter to continue...) after a function executes.
    
    This ensures users have time to read any output before returning to a menu.
    
    Args:
        func: The function to wrap
        
    Returns:
        Wrapped function with pause functionality
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            # Execute the original function
            result = func(*args, **kwargs)
            # Always pause for user to view output
            input("\n⏎ Press Enter to continue...")
            return result
        except (KeyboardInterrupt, EOFError):
            # Handle user interruption gracefully
            print("\nOperation cancelled.")
            input("\n⏎ Press Enter to continue...")
            return None
        except Exception as e:
            # Ensure pause even if there's an error
            debug(f"Error in menu action: {e}")
            input("\n⏎ Press Enter to continue...")
            # Re-raise exception so it can be handled by the caller
            raise
            
    return cast(F, wrapper)

def pause_after_action(message: str = "\n⏎ Press Enter to continue...") -> None:
    """
    Function to pause and wait for user input.
    
    This can be called directly at the end of a menu action function
    when decorator approach isn't suitable.
    
    Args:
        message: Custom message to display (defaults to "Press Enter to continue...")
    """
    try:
        input(message)
    except (KeyboardInterrupt, EOFError):
        # Handle user interruption gracefully
        print("\nOperation cancelled.")
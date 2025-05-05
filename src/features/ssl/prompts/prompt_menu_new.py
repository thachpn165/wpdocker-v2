"""
SSL certificate management menu prompt module.

This module provides the user interface for SSL certificate management functions,
using the new menu utility functions for cleaner code.
"""

from typing import Optional, Dict, Any

from src.common.logging import info, error, debug, success
from src.common.ui.menu_utils import with_pause
from src.common.ui.prompt_helpers import create_menu_handler, create_prompt_menu

def prompt_ssl_menu_new() -> None:
    """Display SSL certificate management menu with improved implementation."""
    options = [
        {"name": "1. Install SSL Certificate", "value": "1"},
        {"name": "2. Check Certificate Info", "value": "2"},
        {"name": "3. Edit Current Certificate", "value": "3"},
    ]
    
    # Define handlers for each option
    handlers = {
        "1": create_menu_handler("src.features.ssl.cli.install", "cli_install_ssl"),
        "2": create_menu_handler("src.features.ssl.cli.check", "cli_check_ssl"),
        "3": create_menu_handler("src.features.ssl.cli.edit", "cli_edit_ssl"),
    }
    
    # Display menu and get selection
    choice = create_prompt_menu("\n🔒 SSL Certificate Management:", options)
    
    # Execute handler for selection if not "Back"
    if choice != "0" and choice in handlers:
        handlers[choice]()

# This is just an example, don't execute it
if __name__ == "__main__":
    prompt_ssl_menu_new()
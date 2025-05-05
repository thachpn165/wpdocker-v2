"""
Example of improved website management menu prompt.

This is an example of how to create a menu using the new helper functions.
"""

from typing import Optional

from src.common.logging import info, error, debug, success
from src.common.ui.menu_utils import with_pause, pause_after_action
from src.common.ui.prompt_helpers import create_menu_handler, create_prompt_menu

def prompt_website_menu_improved() -> None:
    """Display website management menu with improved implementation."""
    options = [
        {"name": "1. Create Website", "value": "1"},
        {"name": "2. Delete Website", "value": "2"},
        {"name": "3. List Websites", "value": "3"},
        {"name": "4. Restart Website", "value": "4"},
        {"name": "5. View Website Logs", "value": "5"},
        {"name": "6. View Website Info", "value": "6"},
        {"name": "7. Migrate Data to WP Docker", "value": "7"},
    ]
    
    # Define handlers for each option
    handlers = {
        "1": create_menu_handler("src.features.website.cli.create", "cli_create_website"),
        "2": create_menu_handler("src.features.website.cli.delete", "cli_delete_website"),
        "3": create_menu_handler("src.features.website.cli.list", "list_websites"),
        "4": create_menu_handler("src.features.website.cli.restart", "cli_restart_website"),
        "5": create_menu_handler("src.features.website.cli.logs", "cli_view_logs"),
        "6": create_menu_handler("src.features.website.cli.info", "cli_website_info"),
        "7": lambda: error("🚧 Feature not implemented yet") or pause_after_action()
    }
    
    # Display menu and get selection
    choice = create_prompt_menu("\n🌐 Website Management:", options)
    
    # Execute handler for selection if not "Back"
    if choice != "0" and choice in handlers:
        handlers[choice]()

# This is just an example, don't execute it
if __name__ == "__main__":
    prompt_website_menu_improved()
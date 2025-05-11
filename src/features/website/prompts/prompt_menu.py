"""
Website management menu prompt module.

This module provides the user interface for website management functions
like creating, deleting, listing, and restarting websites.
"""

import questionary
from questionary import Style

from src.common.logging import error
from src.common.ui.menu_utils import with_pause, pause_after_action

# Import prompts
from src.features.website.prompts.prompt_create import prompt_create_website
from src.features.website.prompts.prompt_delete import prompt_delete_website
from src.features.website.prompts.prompt_restart import prompt_restart_website
from src.features.website.prompts.prompt_logs import prompt_view_logs
from src.features.website.prompts.prompt_info import prompt_website_info
from src.features.website.prompts.prompt_list import prompt_list_websites


@with_pause
def not_implemented() -> None:
    """Handle not implemented features."""
    error("🚧 Feature not implemented yet")


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


def prompt_website_menu() -> None:
    """Display website management menu and handle user selection."""
    try:
        choices = [
            {"name": "1. Create Website", "value": "1"},
            {"name": "2. Delete Website", "value": "2"},
            {"name": "3. List Websites", "value": "3"},
            {"name": "4. Restart Website", "value": "4"},
            {"name": "5. View Website Logs", "value": "5"},
            {"name": "6. View Website Info", "value": "6"},
            {"name": "7. Migrate Data to WP Docker", "value": "7"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]

        answer = questionary.select(
            "\n🌐 Website Management:",
            choices=choices,
            style=custom_style
        ).ask()

        if answer == "1":
            prompt_create_website()
        elif answer == "2":
            prompt_delete_website()
        elif answer == "3":
            prompt_list_websites()
        elif answer == "4":
            prompt_restart_website()
        elif answer == "5":
            prompt_view_logs()
        elif answer == "6":
            prompt_website_info()
        elif answer == "7":
            not_implemented()  # Migrate feature not implemented yet
        # answer "0" just returns to main menu
    except Exception as e:
        error(f"Error in website menu: {e}")
        input("Press Enter to continue...")

"""
Website management menu prompt module.

This module provides the user interface for website management functions
like creating, deleting, listing, and restarting websites.
"""

import questionary
from questionary import Style

from src.common.logging import error
from src.common.ui.menu_utils import with_pause, pause_after_action


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
            try:
                from src.features.website.cli.create import cli_create_website
                cli_create_website()
                pause_after_action()
            except ImportError:
                not_implemented()
        elif answer == "2":
            try:
                from src.features.website.cli.delete import cli_delete_website
                cli_delete_website()
                pause_after_action()
            except ImportError:
                not_implemented()
        elif answer == "3":
            try:
                from src.features.website.cli.list import list_websites
                # Wrap the function call with pause_after_action
                list_websites()
                pause_after_action()
            except ImportError:
                not_implemented()
        elif answer == "4":
            try:
                from src.features.website.cli.restart import cli_restart_website
                cli_restart_website()
            except ImportError:
                not_implemented()
        elif answer == "5":
            try:
                from src.features.website.cli.logs import cli_view_logs
                cli_view_logs()
            except ImportError:
                not_implemented()
        elif answer == "6":
            try:
                from src.features.website.cli.info import cli_website_info
                cli_website_info()
            except ImportError:
                not_implemented()
        elif answer == "7":
            not_implemented()  # Migrate feature not implemented yet
        # answer "0" just returns to main menu
    except Exception as e:
        error(f"Error in website menu: {e}")
        input("Press Enter to continue...")

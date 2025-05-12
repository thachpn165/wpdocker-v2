"""
Main menu for update management.

This module provides the main menu for checking and applying
updates to the WP Docker application.
"""

import time
from typing import Optional

import questionary
from questionary import Style

from src.common.logging import log_call, info, success, error


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


@log_call
def prompt_update_menu() -> None:
    """Display the update management menu."""
    while True:
        choices = [
            {"name": "1. Check for Updates", "value": "1"},
            {"name": "2. Update to Latest Version", "value": "2"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n🔄 Update Management:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "1":
            prompt_check_version()
        elif answer == "2":
            prompt_upgrade()
        elif answer == "0" or answer is None:
            break


@log_call
def prompt_check_version() -> None:
    """Prompt to check for updates."""
    from src.features.update.cli.check import cli_check_version
    
    info("Checking for updates...")
    time.sleep(0.5)  # Small delay for user experience
    
    cli_check_version(interactive=True)
    
    input("\nPress Enter to continue...")


@log_call
def prompt_upgrade() -> None:
    """Prompt to apply updates."""
    from src.features.update.actions import check_version_action
    from src.features.update.cli.upgrade import cli_upgrade
    
    # First check if updates are available
    info("Checking for available updates...")
    time.sleep(0.5)  # Small delay for user experience
    
    check_result = check_version_action()
    
    if not check_result["update_available"]:
        info("You are already using the latest version.")
        input("\nPress Enter to continue...")
        return
        
    # Show update information
    update_info = check_result["update_info"]
    current_version = check_result["current_version"]
    new_version = update_info.get("version", "unknown")
    
    # Ask for confirmation
    confirm = questionary.confirm(
        f"Update from {current_version} to {new_version}?",
        default=True
    ).ask()
    
    if not confirm:
        info("Update cancelled.")
        input("\nPress Enter to continue...")
        return
        
    # Apply the update
    info(f"Updating to version {new_version}...")
    success = cli_upgrade(interactive=True)
    
    if success:
        success("Update completed successfully.")
        info("Please restart the application to use the new version.")
    else:
        error("Update failed. Please try again later or update manually.")
        
    input("\nPress Enter to continue...")
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
    from src.features.update.core.version_updater import VersionUpdater

    info("Checking for updates...")
    time.sleep(0.5)  # Small delay for user experience

    # Use the VersionUpdater's prompt_update function
    updater = VersionUpdater()
    updater.prompt_update()

    input("\nPress Enter to continue...")


@log_call
def prompt_upgrade() -> None:
    """Prompt to apply updates."""
    from src.features.update.actions import check_version_action, update_action
    from src.common.utils.version_helper import get_version, get_display_name

    # First check if updates are available
    info("Checking for updates...")
    time.sleep(0.5)  # Small delay for user experience

    check_result = check_version_action()

    if not check_result["update_available"]:
        info("You are using the latest version.")
        input("\nPress Enter to continue...")
        return

    # Show update information
    update_info = check_result["update_info"]
    current_version = get_version()
    current_display_name = get_display_name()
    new_version = update_info.get("version", "unknown")
    new_display_version = update_info.get("display_version", new_version)
    
    # Tạo mô tả phong phú hơn cho phiên bản mới nếu có metadata
    metadata = update_info.get("metadata", {})
    version_description = new_display_version
    channel = update_info.get("channel", "stable")
    
    # Thêm code_name nếu có và chưa có trong display_version
    if metadata and "code_name" in metadata and metadata["code_name"] not in new_display_version:
        version_description += f" \"{metadata['code_name']}\""
    
    # Thêm thông tin kênh và build nếu có
    if channel == "nightly" and metadata and "build_number" in metadata:
        if f"Build {metadata['build_number']}" not in new_display_version:
            version_description += f" (Build {metadata['build_number']})"
    elif channel != "stable" and "nightly" not in new_display_version.lower():
        version_description += f" ({channel.capitalize()})"
    
    # Thêm thông tin ngày build cho nightly builds
    if channel == "nightly" and metadata and "build_date" in metadata:
        if metadata["build_date"] not in new_display_version:
            date_parts = metadata["build_date"].split("-")
            if len(date_parts) == 3:
                formatted_date = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
                if formatted_date not in new_display_version:
                    version_description += f" - {formatted_date}"

    # Ask for confirmation
    confirm = questionary.confirm(
        f"Update from {current_display_name} to {version_description}?",
        default=True
    ).ask()

    if not confirm:
        info("Update cancelled.")
        input("\nPress Enter to continue...")
        return

    # Apply the update
    info(f"Updating to version {new_version}...")
    result = update_action()

    if result["success"]:
        success("Update completed successfully.")
        info("Please restart the application to use the new version.")
    else:
        error(f"Update failed: {result['message']}")

    input("\nPress Enter to continue...")
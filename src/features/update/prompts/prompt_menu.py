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
    from src.features.update.core.version_updater import prompt_update

    info("Kiểm tra cập nhật...")
    time.sleep(0.5)  # Small delay for user experience

    # Use the VersionUpdater's prompt_update function
    prompt_update()

    input("\nNhấn Enter để tiếp tục...")


@log_call
def prompt_upgrade() -> None:
    """Prompt to apply updates."""
    from src.features.update.actions import check_version_action, update_action
    from src.version import VERSION

    # First check if updates are available
    info("Đang kiểm tra bản cập nhật...")
    time.sleep(0.5)  # Small delay for user experience

    check_result = check_version_action()

    if not check_result["update_available"]:
        info("Bạn đang sử dụng phiên bản mới nhất.")
        input("\nNhấn Enter để tiếp tục...")
        return

    # Show update information
    update_info = check_result["update_info"]
    current_version = VERSION
    new_version = update_info.get("version", "unknown")

    # Ask for confirmation
    confirm = questionary.confirm(
        f"Cập nhật từ {current_version} lên {new_version}?",
        default=True
    ).ask()

    if not confirm:
        info("Đã hủy cập nhật.")
        input("\nNhấn Enter để tiếp tục...")
        return

    # Apply the update
    info(f"Đang cập nhật lên phiên bản {new_version}...")
    result = update_action()

    if result["success"]:
        success("Cập nhật hoàn tất thành công.")
        info("Vui lòng khởi động lại ứng dụng để sử dụng phiên bản mới.")
    else:
        error(f"Cập nhật thất bại: {result['message']}")

    input("\nNhấn Enter để tiếp tục...")
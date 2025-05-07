"""
CLI commands cho menu operations.
"""
from typing import List, Dict, Any, Optional
import questionary
from questionary import Style

from src.common.logging import info, error, debug, success

# Import các commands
from src.features.rclone.cli.remote import (
    add_remote,
    remove_remote,
    list_remotes,
    show_remote_info
)
from src.features.rclone.cli.file import (
    list_files,
    copy_file,
    move_file,
    delete_file
)
from src.features.rclone.cli.sync import (
    sync_to_remote,
    sync_from_remote,
    sync_between_remotes
)
from src.features.rclone.cli.mount import (
    mount_remote,
    unmount_remote,
    list_mounts
)
from src.features.rclone.cli.config import (
    show_config,
    show_remote_config,
    edit_config,
    edit_remote_config
)
from src.features.rclone.cli.system import (
    check_installation,
    install_rclone,
    update_rclone,
    uninstall_rclone
)

# Custom style cho questionary
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),     # token in front of the question
    ('question', 'bold'),             # question text
    ('answer', 'fg:#f44336 bold'),    # submitted answer text behind the question
    ('pointer', 'fg:#673ab7 bold'),   # pointer used in select and checkbox prompts
    ('highlighted', 'fg:#673ab7 bold'),  # pointed-at choice in select and checkbox prompts
    ('selected', 'fg:#cc5454'),       # style for a selected item of a checkbox
    ('separator', 'fg:#cc5454'),      # separator in lists
    ('instruction', ''),              # user instructions for select, rawselect, checkbox
    ('text', ''),                     # plain text
    ('disabled', 'fg:#858585 italic'), # disabled choices for select and checkbox prompts
])

def show_remote_menu() -> None:
    """
    Hiển thị menu quản lý remote.
    """
    while True:
        # Hiển thị menu
        choice = questionary.select(
            "Remote Management",
            choices=[
                "Add Remote",
                "Remove Remote",
                "List Remotes",
                "Show Remote Info",
                "Back"
            ],
            style=custom_style
        ).ask()
        
        if choice == "Add Remote":
            add_remote()
        elif choice == "Remove Remote":
            remove_remote()
        elif choice == "List Remotes":
            list_remotes()
        elif choice == "Show Remote Info":
            show_remote_info()
        elif choice == "Back":
            break

def show_file_menu() -> None:
    """
    Hiển thị menu quản lý file.
    """
    while True:
        # Hiển thị menu
        choice = questionary.select(
            "File Management",
            choices=[
                "List Files",
                "Copy File",
                "Move File",
                "Delete File",
                "Back"
            ],
            style=custom_style
        ).ask()
        
        if choice == "List Files":
            list_files()
        elif choice == "Copy File":
            copy_file()
        elif choice == "Move File":
            move_file()
        elif choice == "Delete File":
            delete_file()
        elif choice == "Back":
            break

def show_sync_menu() -> None:
    """
    Hiển thị menu quản lý sync.
    """
    while True:
        # Hiển thị menu
        choice = questionary.select(
            "Sync Management",
            choices=[
                "Sync to Remote",
                "Sync from Remote",
                "Sync Between Remotes",
                "Back"
            ],
            style=custom_style
        ).ask()
        
        if choice == "Sync to Remote":
            sync_to_remote()
        elif choice == "Sync from Remote":
            sync_from_remote()
        elif choice == "Sync Between Remotes":
            sync_between_remotes()
        elif choice == "Back":
            break

def show_mount_menu() -> None:
    """
    Hiển thị menu quản lý mount.
    """
    while True:
        # Hiển thị menu
        choice = questionary.select(
            "Mount Management",
            choices=[
                "Mount Remote",
                "Unmount Remote",
                "List Mounts",
                "Back"
            ],
            style=custom_style
        ).ask()
        
        if choice == "Mount Remote":
            mount_remote()
        elif choice == "Unmount Remote":
            unmount_remote()
        elif choice == "List Mounts":
            list_mounts()
        elif choice == "Back":
            break

def show_config_menu() -> None:
    """
    Hiển thị menu quản lý config.
    """
    while True:
        # Hiển thị menu
        choice = questionary.select(
            "Config Management",
            choices=[
                "Show Config",
                "Show Remote Config",
                "Edit Config",
                "Edit Remote Config",
                "Back"
            ],
            style=custom_style
        ).ask()
        
        if choice == "Show Config":
            show_config()
        elif choice == "Show Remote Config":
            show_remote_config()
        elif choice == "Edit Config":
            edit_config()
        elif choice == "Edit Remote Config":
            edit_remote_config()
        elif choice == "Back":
            break

def show_system_menu() -> None:
    """
    Hiển thị menu quản lý system.
    """
    while True:
        # Hiển thị menu
        choice = questionary.select(
            "System Management",
            choices=[
                "Check Installation",
                "Install Rclone",
                "Update Rclone",
                "Uninstall Rclone",
                "Back"
            ],
            style=custom_style
        ).ask()
        
        if choice == "Check Installation":
            check_installation()
        elif choice == "Install Rclone":
            install_rclone()
        elif choice == "Update Rclone":
            update_rclone()
        elif choice == "Uninstall Rclone":
            uninstall_rclone()
        elif choice == "Back":
            break

def show_main_menu() -> None:
    """
    Hiển thị menu chính.
    """
    while True:
        # Hiển thị menu
        choice = questionary.select(
            "Rclone Management",
            choices=[
                "Remote Management",
                "File Management",
                "Sync Management",
                "Mount Management",
                "Config Management",
                "System Management",
                "Exit"
            ],
            style=custom_style
        ).ask()
        
        if choice == "Remote Management":
            show_remote_menu()
        elif choice == "File Management":
            show_file_menu()
        elif choice == "Sync Management":
            show_sync_menu()
        elif choice == "Mount Management":
            show_mount_menu()
        elif choice == "Config Management":
            show_config_menu()
        elif choice == "System Management":
            show_system_menu()
        elif choice == "Exit":
            break 
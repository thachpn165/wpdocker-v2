"""
Backup management menu prompt module.

This module provides the user interface for backup and restore functions
like creating backups, restoring backups, and scheduling automatic backups.
"""

import questionary
from questionary import Style
from typing import Optional

from src.common.logging import info, error, debug, success

def not_implemented() -> None:
    """Handle not implemented features."""
    error("🚧 Feature not implemented yet")
    input("Press Enter to continue...")

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

def prompt_cloud_backup() -> None:
    """Handle cloud backup menu."""
    try:
        # Try to import the original cloud backup prompt
        from src.features.backup.prompts.prompt_cloud_backup import prompt_cloud_backup as original_prompt
        original_prompt()
    except ImportError:
        error("Cloud backup not implemented yet")
        input("Press Enter to continue...")

def prompt_backup_menu() -> None:
    """Display backup management menu and handle user selection."""
    try:
        try:
            from src.features.backup.prompts.prompt_backup_website import prompt_backup_website
            
            choices = [
                {"name": "1. Create Website Backup", "value": "1"},
                {"name": "2. Restore Backup", "value": "2"},
                {"name": "3. List Backups", "value": "3"},
                {"name": "4. Delete Backup", "value": "4"},
                {"name": "5. Schedule Automatic Backup", "value": "5"},
                {"name": "6. Cloud Backup with RClone", "value": "6"},
                {"name": "0. Back to Main Menu", "value": "0"},
            ]
            
            answer = questionary.select(
                "\n💾 Backup Management:",
                choices=choices,
                style=custom_style
            ).ask()
            
            if answer == "1":
                prompt_backup_website()
            elif answer == "6":
                prompt_cloud_backup()
            elif answer != "0":
                not_implemented()
        except ImportError:
            error("Backup module not fully implemented yet")
            input("Press Enter to continue...")
    except Exception as e:
        error(f"Error in backup menu: {e}")
        input("Press Enter to continue...")
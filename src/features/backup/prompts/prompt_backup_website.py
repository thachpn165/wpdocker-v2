"""
Backup website prompt module.

This module provides the user interface for backing up websites.
"""

import os
import questionary
from questionary import Style
from typing import Optional

from src.common.logging import info, error, debug, success
from src.features.backup.website_backup import backup_website
from src.features.website.utils import select_website

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

def prompt_backup_website() -> None:
    """Prompt to create website backup."""
    info("\n📋 Create Website Backup")
    
    # Get selected website using the utility function
    selected_website = select_website("Select website to backup:")
    
    if not selected_website:
        info("Operation cancelled or no websites found.")
        input("\nPress Enter to continue...")
        return
    
    # Create backup
    info(f"🚀 Creating backup for website: {selected_website}")
    backup_path = backup_website(selected_website)
    
    if backup_path:
        success(f"✅ Backup created successfully: {os.path.basename(backup_path)}")
        
        # Ask if user wants to upload to cloud
        if questionary.confirm(
            "Would you like to upload this backup to cloud storage?",
            style=custom_style,
            default=False
        ).ask():
            from src.features.backup.prompts.prompt_menu import prompt_cloud_backup_upload
            prompt_cloud_backup_upload(selected_website, backup_path)
    else:
        error("❌ Backup creation failed")
    
    input("\nPress Enter to continue...")
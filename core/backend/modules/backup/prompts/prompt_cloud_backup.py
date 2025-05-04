#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import inquirer
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from core.backend.modules.backup.backup_manager import BackupManager
from core.backend.modules.website.website_utils import website_list
from core.backend.modules.rclone.rclone_manager import RcloneManager
from core.backend.modules.rclone.backup_integration import RcloneBackupIntegration
from core.backend.utils.env_utils import get_env_value
from core.backend.utils.debug import Debug


def prompt_cloud_backup():
    """Prompt for cloud backup operations."""
    actions = [
        "Backup website to cloud storage",
        "Restore website from cloud storage",
        "List cloud backups",
        "Schedule automatic cloud backup",
        "Back to backup menu"
    ]
    
    questions = [
        inquirer.List(
            "action",
            message="Select a cloud backup action:",
            choices=actions,
        ),
    ]
    
    answers = inquirer.prompt(questions)
    
    if answers:
        action = answers["action"]
        
        if action == "Backup website to cloud storage":
            prompt_backup_to_cloud()
        elif action == "Restore website from cloud storage":
            prompt_restore_from_cloud()
        elif action == "List cloud backups":
            prompt_list_cloud_backups()
        elif action == "Schedule automatic cloud backup":
            prompt_schedule_cloud_backup()
        elif action == "Back to backup menu":
            return
    
    # Return to the cloud backup menu unless we're going back
    if answers and answers["action"] != "Back to backup menu":
        prompt_cloud_backup()


def prompt_backup_to_cloud():
    """Prompt for backing up a website to cloud storage."""
    debug = Debug("CloudBackup")
    
    # Check if Rclone is available
    rclone_manager = RcloneManager()
    remotes = rclone_manager.list_remotes()
    
    if not remotes:
        print("\n❌ No Rclone remotes configured. Please add a remote in the Rclone management menu first.")
        input("\nPress Enter to continue...")
        return
    
    # Get websites
    websites = website_list()
    if not websites:
        print("\n❌ No websites found.")
        input("\nPress Enter to continue...")
        return
    
    # Select website to backup
    website_choices = websites
    website_choices.append("Cancel")
    
    website_question = [
        inquirer.List(
            "website",
            message="Select website to backup:",
            choices=website_choices,
        ),
    ]
    
    website_answer = inquirer.prompt(website_question)
    
    if not website_answer or website_answer["website"] == "Cancel":
        return
    
    website_name = website_answer["website"]
    
    # Select remote
    remote_question = [
        inquirer.List(
            "remote",
            message="Select destination remote:",
            choices=remotes + ["Cancel"],
        ),
    ]
    
    remote_answer = inquirer.prompt(remote_question)
    
    if not remote_answer or remote_answer["remote"] == "Cancel":
        return
    
    remote_name = remote_answer["remote"]
    
    # Create backup
    print(f"\n📦 Creating backup of {website_name}...")
    
    backup_manager = BackupManager()
    backup_path = backup_manager.backup_website(website_name)
    
    if not backup_path:
        print(f"\n❌ Failed to create backup of {website_name}")
        input("\nPress Enter to continue...")
        return
    
    # Upload to remote
    print(f"\n🚀 Uploading backup to {remote_name}...")
    
    integration = RcloneBackupIntegration()
    success, message = integration.backup_to_remote(remote_name, website_name, backup_path)
    
    if success:
        print(f"\n✅ {message}")
    else:
        print(f"\n❌ {message}")
    
    input("\nPress Enter to continue...")


def prompt_restore_from_cloud():
    """Prompt for restoring a website from cloud storage."""
    debug = Debug("CloudRestore")
    
    # Check if Rclone is available
    rclone_manager = RcloneManager()
    remotes = rclone_manager.list_remotes()
    
    if not remotes:
        print("\n❌ No Rclone remotes configured. Please add a remote in the Rclone management menu first.")
        input("\nPress Enter to continue...")
        return
    
    # Select remote
    remote_question = [
        inquirer.List(
            "remote",
            message="Select source remote:",
            choices=remotes + ["Cancel"],
        ),
    ]
    
    remote_answer = inquirer.prompt(remote_question)
    
    if not remote_answer or remote_answer["remote"] == "Cancel":
        return
    
    remote_name = remote_answer["remote"]
    
    # List backups on the remote
    print(f"\n🔍 Listing backups on {remote_name}...")
    
    integration = RcloneBackupIntegration()
    
    # Get website directories in the backups folder
    website_dirs = rclone_manager.list_files(remote_name, "backups")
    
    if not website_dirs:
        print(f"\n❌ No backups found on {remote_name}")
        input("\nPress Enter to continue...")
        return
    
    # Filter for directories only
    website_dirs = [d for d in website_dirs if d.get("IsDir", False)]
    
    if not website_dirs:
        print(f"\n❌ No website backup directories found on {remote_name}")
        input("\nPress Enter to continue...")
        return
    
    # Select website backup directory
    website_choices = [d.get("Name") for d in website_dirs]
    website_choices.append("Cancel")
    
    website_question = [
        inquirer.List(
            "website",
            message="Select website backup directory:",
            choices=website_choices,
        ),
    ]
    
    website_answer = inquirer.prompt(website_question)
    
    if not website_answer or website_answer["website"] == "Cancel":
        return
    
    website_name = website_answer["website"]
    
    # List backup files for the selected website
    backup_files = rclone_manager.list_files(remote_name, f"backups/{website_name}")
    
    if not backup_files:
        print(f"\n❌ No backup files found for {website_name} on {remote_name}")
        input("\nPress Enter to continue...")
        return
    
    # Filter for non-directories
    backup_files = [f for f in backup_files if not f.get("IsDir", False)]
    
    if not backup_files:
        print(f"\n❌ No backup files found for {website_name} on {remote_name}")
        input("\nPress Enter to continue...")
        return
    
    # Create display entries for backup files with date and size
    backup_choices = []
    for backup in backup_files:
        name = backup.get("Name", "Unknown")
        size = backup.get("Size", 0)
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.2f} MB"
        else:
            size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
        
        modified = backup.get("ModTime", "Unknown")
        backup_choices.append(f"{name} ({size_str}, {modified})")
    
    backup_choices.append("Cancel")
    
    # Select backup file
    backup_question = [
        inquirer.List(
            "backup",
            message="Select backup file to restore:",
            choices=backup_choices,
        ),
    ]
    
    backup_answer = inquirer.prompt(backup_question)
    
    if not backup_answer or backup_answer["backup"] == "Cancel":
        return
    
    # Extract just the filename from the selected backup
    selected_backup = backup_answer["backup"].split(" ")[0]
    
    # Confirm restoration
    confirm_question = [
        inquirer.Confirm(
            "confirm",
            message=f"Are you sure you want to restore {selected_backup} for {website_name}?",
            default=False
        ),
    ]
    
    confirm_answer = inquirer.prompt(confirm_question)
    
    if not confirm_answer or not confirm_answer["confirm"]:
        return
    
    # Download backup file
    print(f"\n📥 Downloading backup file {selected_backup}...")
    
    backup_dir = get_env_value("BACKUP_DIR")
    local_path = os.path.join(backup_dir, selected_backup)
    
    success, message = integration.restore_from_remote(
        remote_name, 
        f"backups/{website_name}/{selected_backup}", 
        local_path
    )
    
    if not success:
        print(f"\n❌ {message}")
        input("\nPress Enter to continue...")
        return
    
    # Restore website from the downloaded backup
    print(f"\n🔄 Restoring website from backup...")
    
    backup_manager = BackupManager()
    restore_success = backup_manager.restore_website(website_name, local_path)
    
    if restore_success:
        print(f"\n✅ Website {website_name} restored successfully from cloud backup")
    else:
        print(f"\n❌ Failed to restore website {website_name} from cloud backup")
    
    input("\nPress Enter to continue...")


def prompt_list_cloud_backups():
    """Prompt for listing cloud backups."""
    debug = Debug("CloudBackupList")
    
    # Check if Rclone is available
    rclone_manager = RcloneManager()
    remotes = rclone_manager.list_remotes()
    
    if not remotes:
        print("\n❌ No Rclone remotes configured. Please add a remote in the Rclone management menu first.")
        input("\nPress Enter to continue...")
        return
    
    # Select remote
    remote_question = [
        inquirer.List(
            "remote",
            message="Select remote to list backups from:",
            choices=remotes + ["Cancel"],
        ),
    ]
    
    remote_answer = inquirer.prompt(remote_question)
    
    if not remote_answer or remote_answer["remote"] == "Cancel":
        return
    
    remote_name = remote_answer["remote"]
    
    # List backups on the remote
    print(f"\n🔍 Listing backups on {remote_name}...")
    
    # Get website directories in the backups folder
    website_dirs = rclone_manager.list_files(remote_name, "backups")
    
    if not website_dirs:
        print(f"\n❌ No backups found on {remote_name}")
        input("\nPress Enter to continue...")
        return
    
    # Filter for directories only
    website_dirs = [d for d in website_dirs if d.get("IsDir", False)]
    
    if not website_dirs:
        print(f"\n❌ No website backup directories found on {remote_name}")
        input("\nPress Enter to continue...")
        return
    
    # Print websites and their backups
    print(f"\n📁 Cloud backups on {remote_name}:")
    
    for website_dir in website_dirs:
        website_name = website_dir.get("Name")
        print(f"\n  📂 {website_name}")
        
        # Get backup files for this website
        backup_files = rclone_manager.list_files(remote_name, f"backups/{website_name}")
        
        if not backup_files:
            print("     No backups found")
            continue
        
        # Filter for non-directories and sort by modification time (newest first)
        backup_files = [f for f in backup_files if not f.get("IsDir", False)]
        backup_files.sort(key=lambda x: x.get("ModTime", ""), reverse=True)
        
        if not backup_files:
            print("     No backups found")
            continue
        
        # Print backup files
        for backup in backup_files:
            name = backup.get("Name", "Unknown")
            size = backup.get("Size", 0)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.2f} KB"
            elif size < 1024 * 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.2f} MB"
            else:
                size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
            
            modified = backup.get("ModTime", "Unknown")
            print(f"     📄 {name} ({size_str}, {modified})")
    
    input("\nPress Enter to continue...")


def prompt_schedule_cloud_backup():
    """Prompt for scheduling cloud backups."""
    debug = Debug("CloudBackupSchedule")
    
    # Check if Rclone is available
    rclone_manager = RcloneManager()
    remotes = rclone_manager.list_remotes()
    
    if not remotes:
        print("\n❌ No Rclone remotes configured. Please add a remote in the Rclone management menu first.")
        input("\nPress Enter to continue...")
        return
    
    # Get websites
    websites = website_list()
    if not websites:
        print("\n❌ No websites found.")
        input("\nPress Enter to continue...")
        return
    
    # Select website to backup
    website_choices = websites
    website_choices.append("Cancel")
    
    website_question = [
        inquirer.List(
            "website",
            message="Select website to schedule backups for:",
            choices=website_choices,
        ),
    ]
    
    website_answer = inquirer.prompt(website_question)
    
    if not website_answer or website_answer["website"] == "Cancel":
        return
    
    website_name = website_answer["website"]
    
    # Select remote
    remote_question = [
        inquirer.List(
            "remote",
            message="Select destination remote:",
            choices=remotes + ["Cancel"],
        ),
    ]
    
    remote_answer = inquirer.prompt(remote_question)
    
    if not remote_answer or remote_answer["remote"] == "Cancel":
        return
    
    remote_name = remote_answer["remote"]
    
    # Select schedule
    schedule_choices = [
        "Daily (at midnight)",
        "Weekly (Sunday at midnight)",
        "Monthly (1st day at midnight)",
        "Custom schedule",
        "Cancel"
    ]
    
    schedule_question = [
        inquirer.List(
            "schedule",
            message="Select backup schedule:",
            choices=schedule_choices,
        ),
    ]
    
    schedule_answer = inquirer.prompt(schedule_question)
    
    if not schedule_answer or schedule_answer["schedule"] == "Cancel":
        return
    
    # Convert schedule choice to cron expression
    if schedule_answer["schedule"] == "Daily (at midnight)":
        cron_schedule = "0 0 * * *"
    elif schedule_answer["schedule"] == "Weekly (Sunday at midnight)":
        cron_schedule = "0 0 * * 0"
    elif schedule_answer["schedule"] == "Monthly (1st day at midnight)":
        cron_schedule = "0 0 1 * *"
    elif schedule_answer["schedule"] == "Custom schedule":
        # Prompt for custom schedule
        custom_question = [
            inquirer.Text(
                "custom",
                message="Enter cron schedule (e.g., '0 0 * * *' for daily at midnight):",
                validate=lambda _, x: len(x.strip().split()) == 5
            ),
        ]
        
        custom_answer = inquirer.prompt(custom_question)
        
        if not custom_answer:
            return
        
        cron_schedule = custom_answer["custom"]
    else:
        return
    
    # Schedule the backup
    integration = RcloneBackupIntegration()
    success, message = integration.schedule_remote_backup(remote_name, website_name, cron_schedule)
    
    if success:
        print(f"\n✅ {message}")
    else:
        print(f"\n❌ {message}")
    
    input("\nPress Enter to continue...")
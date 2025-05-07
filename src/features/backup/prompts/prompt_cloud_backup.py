"""
Cloud backup management prompts.

This module provides interactive prompts for managing cloud backups,
including backup creation, restoration, listing, and scheduling.
"""

import os
import inquirer
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from src.common.logging import Debug
from src.common.utils.environment import get_env_value


def prompt_restore_from_cloud():
    """
    Prompt for restoring a website from cloud storage.
    
    Guides the user through selecting a remote, website, and backup file,
    then handles the restoration process.
    """
    debug = Debug("CloudRestore")
    
    # Import here to avoid circular imports
    from src.features.website.utils import website_list
    from src.features.rclone.manager import RcloneManager
    from src.features.rclone.backup_integration import RcloneBackupIntegration
    from src.common.ui.menu_utils import pause_after_action
    # Check if Rclone is available
    rclone_manager = RcloneManager()
    remotes = rclone_manager.list_remotes()
    
    if not remotes:
        debug.error("\n❌ No Rclone remotes configured. Please add a remote in the Rclone management menu first.")
        pause_after_action()
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
    debug.info(f"\n🔍 Listing backups on {remote_name}...")
    
    integration = RcloneBackupIntegration()
    
    # Get website directories in the backups folder
    website_dirs = rclone_manager.list_files(remote_name, "backups")
    
    if not website_dirs:
        debug.error(f"\n❌ No backups found on {remote_name}")
        pause_after_action()
        return
    
    # Filter for directories only
    website_dirs = [d for d in website_dirs if d.get("IsDir", False)]
    
    if not website_dirs:
        debug.error(f"\n❌ No website backup directories found on {remote_name}")
        pause_after_action()
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
        debug.error(f"\n❌ No backup files found for {website_name} on {remote_name}")
        pause_after_action()
        return
    
    # Filter non-directory files
    backup_files = [f for f in backup_files if not f.get("IsDir", False)]
    
    if not backup_files:
        debug.error(f"\n❌ No backup files found for {website_name} on {remote_name}")
        pause_after_action()
        return
    
    # Sort backup files by modification time (newest first)
    backup_files.sort(key=lambda x: x.get("ModTime", ""), reverse=True)
    
    # Prepare a list of backup files with detailed information for display
    backup_choices = []
    backup_files_dict = {}  # Keep a mapping of display string to actual backup file and path
    
    for backup in backup_files:
        name = backup.get("Name", "Unknown")
        path = f"backups/{website_name}/{name}"  # Consistent path format
        size = backup.get("Size", 0)
        
        # Format file size for display
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.2f} MB"
        else:
            size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
        
        # Parse and format modification time
        modified_str = backup.get("ModTime", "Unknown")
        try:
            # Parse ISO 8601 format timestamp
            mod_time = datetime.strptime(modified_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
            friendly_date = mod_time.strftime("%d/%m/%Y %H:%M:%S")
        except:
            friendly_date = modified_str
        
        # Determine backup type for display
        backup_type = ""
        if name.endswith(".sql"):
            backup_type = "[Database]"
        elif name.endswith(".tar.gz") or name.endswith(".tgz"):
            backup_type = "[Files]"
        
        # Create display string with all information
        display = f"{name} {backup_type} - {friendly_date} ({size_str})"
        backup_choices.append(display)
        backup_files_dict[display] = {"name": name, "path": path}  # Store both name and path
    
    # Add cancel option
    backup_choices.append("Cancel")
    
    # Print a summary of available backups
    debug.info(f"\n📋 Found {len(backup_files)} backup files for {website_name}:")
    
    # Group backups by type
    database_backups = [b for b in backup_files if b.get("Name", "").endswith(".sql")]
    files_backups = [b for b in backup_files if b.get("Name", "").endswith((".tar.gz", ".tgz"))]
    
    if database_backups:
        most_recent_db = database_backups[0]
        db_name = most_recent_db.get("Name", "Unknown")
        db_date = "Unknown"
        try:
            mod_time = datetime.strptime(most_recent_db.get("ModTime", "").split(".")[0], "%Y-%m-%dT%H:%M:%S")
            db_date = mod_time.strftime("%d/%m/%Y %H:%M:%S")
        except:
            pass
        debug.info(f"   Most recent database backup: {db_name} (created on {db_date})")
    
    if files_backups:
        most_recent_file = files_backups[0]
        file_name = most_recent_file.get("Name", "Unknown")
        file_date = "Unknown"
        try:
            mod_time = datetime.strptime(most_recent_file.get("ModTime", "").split(".")[0], "%Y-%m-%dT%H:%M:%S")
            file_date = mod_time.strftime("%d/%m/%Y %H:%M:%S")
        except:
            pass
        debug.info(f"   Most recent files backup: {file_name} (created on {file_date})")
    
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
    
    # Extract the filename and path from the selected backup using our mapping dictionary
    selected_display = backup_answer["backup"]
    if selected_display == "Cancel":
        return
    
    if selected_display not in backup_files_dict:
        debug.error(f"\n❌ Error: Cannot find selected backup information")
        pause_after_action()
        return
        
    selected_backup_info = backup_files_dict[selected_display]
    selected_backup_name = selected_backup_info.get("name")
    selected_backup_path = selected_backup_info.get("path")
    
    # Check for missing information
    if not selected_backup_name:
        debug.error(f"\n❌ Error: Backup name is missing")
        pause_after_action()
        return
    
    # Find the full backup information for display in confirmation
    selected_backup_full = next((b for b in backup_files if b.get("Name") == selected_backup_name), None)
    if selected_backup_full:
        # Get the modification time for confirmation message
        modified_str = selected_backup_full.get("ModTime", "Unknown")
        try:
            mod_time = datetime.strptime(modified_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
            backup_date = mod_time.strftime("%d/%m/%Y %H:%M:%S")
        except:
            backup_date = modified_str
        
        backup_type = "Database" if selected_backup_name.endswith(".sql") else "Files" if selected_backup_name.endswith((".tar.gz", ".tgz")) else "Unknown"
    else:
        backup_date = "Unknown date"
        backup_type = "Unknown type"
    
    # Define standard paths
    sites_dir = get_env_value("SITES_DIR")
    wordpress_dir = os.path.join(sites_dir, website_name, "wordpress")
    
    debug.info(f"\n📋 Backup Details:")
    debug.info(f"   Website: {website_name}")
    debug.info(f"   Backup file: {selected_backup_name}")
    debug.info(f"   Type: {backup_type}")
    debug.info(f"   Created: {backup_date}")
    debug.info(f"   Source: {remote_name}:{selected_backup_path}")
    debug.info(f"   Standard restore path: {wordpress_dir}")
    
    confirm_question = [
        inquirer.Confirm(
            "confirm",
            message=f"Are you sure you want to restore this {backup_type} backup (created on {backup_date}) for {website_name}?",
            default=False
        ),
    ]
    
    confirm_answer = inquirer.prompt(confirm_question)
    
    if not confirm_answer or not confirm_answer["confirm"]:
        return
    
    # Download backup file
    debug.info(f"\n📥 Downloading backup file {selected_backup_name}...")
    
    # Use website's backup directory instead of BACKUP_DIR
    if not sites_dir:
        debug.error("\n❌ Error: SITES_DIR environment variable is not set")
        pause_after_action()
        return
    
    # Create path to website's backup directory
    website_backup_dir = os.path.join(sites_dir, website_name, "backups")
    
    # Ensure backup directory exists
    if not os.path.exists(website_backup_dir):
        try:
            os.makedirs(website_backup_dir, exist_ok=True)
            debug.success(f"\n✅ Created backup directory: {website_backup_dir}")
        except Exception as e:
            debug.error(f"\n❌ Error creating backup directory: {str(e)}")
            pause_after_action()
            return
    
    local_path = os.path.join(website_backup_dir, selected_backup_name)
    
    # Check if website directory exists
    website_dir = os.path.join(sites_dir, website_name)
    if not os.path.exists(website_dir):
        try:
            os.makedirs(website_dir, exist_ok=True)
            debug.success(f"\n✅ Created website directory: {website_dir}")
        except Exception as e:
            debug.error(f"\n❌ Error creating website directory: {str(e)}")
            pause_after_action()
            return
    
    # Download backup file
    success, message = integration.restore_from_remote(
        remote_name, 
        selected_backup_path, 
        local_path,
        website_name
    )
    
    if not success:
        debug.error(f"\n❌ {message}")
        pause_after_action()
        return
    
    # Restore website from the downloaded backup
    debug.info(f"\n🔄 Restoring website from backup...")
    
    try:
        # Determine backup type
        is_database = selected_backup_name.endswith('.sql')
        is_archive = selected_backup_name.endswith('.tar.gz') or selected_backup_name.endswith('.tgz')
        
        if is_database:
            # Restore database directly using MySQL module
            from src.features.mysql.import_export import import_database
            debug.info(f"\n🗃️ Restoring database from {selected_backup_name}...")
            import_database(website_name, local_path, reset=True)
            restore_success = True
            
        elif is_archive:
            # Restore source code using specialized functions
            from src.features.backup.backup_restore import restore_source_code
            debug.info(f"\n📦 Extracting WordPress files from {selected_backup_name}...")
            restore_success = restore_source_code(website_name, local_path)
            
        else:
            debug.error(f"\n❌ Unknown backup file type: {selected_backup_name}")
            restore_success = False
        
        # If restoration was successful, restart the website
        if restore_success:
            debug.info(f"\n🔄 Restarting website {website_name}...")
            from src.features.backup.backup_restore import restart_website
            restart_result = restart_website(website_name)
            
            if restart_result:
                debug.success(f"\n✅ Website {website_name} restarted successfully")
            else:
                debug.warn(f"\n⚠️ Website restored but could not be restarted automatically")
            
            debug.success(f"\n✅ Website {website_name} restored successfully from cloud backup")
        else:
            debug.error(f"\n❌ Failed to restore website {website_name} from cloud backup")
    
    except Exception as e:
        debug.error(f"\n❌ Error during restoration: {str(e)}")
    
    pause_after_action()
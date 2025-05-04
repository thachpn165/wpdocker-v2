#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import inquirer
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from core.backend.modules.backup.backup_manager import BackupManager
from core.backend.modules.website.website_utils import website_list
from core.backend.modules.rclone.rclone_manager import RcloneManager
from core.backend.modules.rclone.config_manager import RcloneConfigManager
from core.backend.modules.rclone.backup_integration import RcloneBackupIntegration
from core.backend.modules.rclone.utils import get_remote_type_display_name
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
    
    # List backup directories for the selected website
    backup_dirs = rclone_manager.list_files(remote_name, f"backups/{website_name}")
    
    if not backup_dirs:
        print(f"\n❌ No backup directories found for {website_name} on {remote_name}")
        input("\nPress Enter to continue...")
        return
    
    # Kiểm tra xem có thư mục backup không
    backup_dirs_filtered = [d for d in backup_dirs if d.get("IsDir", False)]
    
    if not backup_dirs_filtered:
        # Không có thư mục con, có thể backup files nằm trực tiếp trong thư mục website
        backup_files = backup_dirs
        # Lọc lấy các file (không phải thư mục)
        backup_files = [f for f in backup_files if not f.get("IsDir", False)]
    else:
        # Có thư mục backup, hỏi người dùng chọn thư mục backup
        backup_dir_choices = [(d.get("Name"), d.get("ModTime", "")) for d in backup_dirs_filtered]
        # Sắp xếp theo thời gian mới nhất
        backup_dir_choices.sort(key=lambda x: x[1], reverse=True)
        
        # Chuẩn bị danh sách thư mục backup để hiển thị
        backup_dir_display = []
        for name, mod_time in backup_dir_choices:
            try:
                # Parse time từ ModTime nếu có thể
                from datetime import datetime
                mod_time_str = mod_time.split(".")[0]
                date_obj = datetime.strptime(mod_time_str, "%Y-%m-%dT%H:%M:%S")
                friendly_date = date_obj.strftime("%d/%m/%Y %H:%M:%S")
                display = f"{name} (created on {friendly_date})"
            except:
                display = name
            backup_dir_display.append(display)
        
        backup_dir_display.append("Cancel")
        
        # Hỏi người dùng chọn thư mục backup
        backup_dir_question = [
            inquirer.List(
                "backup_dir",
                message="Select backup directory:",
                choices=backup_dir_display,
            ),
        ]
        
        backup_dir_answer = inquirer.prompt(backup_dir_question)
        
        if not backup_dir_answer or backup_dir_answer["backup_dir"] == "Cancel":
            return
        
        # Lấy tên thư mục từ lựa chọn (loại bỏ phần thời gian)
        selected_dir = backup_dir_answer["backup_dir"].split(" (created on ")[0]
        
        # Liệt kê file trong thư mục backup được chọn
        backup_files = rclone_manager.list_files(remote_name, f"backups/{website_name}/{selected_dir}")
        
        if not backup_files:
            print(f"\n❌ No backup files found in directory {selected_dir}")
            input("\nPress Enter to continue...")
            return
    
    # Lọc các file (không phải thư mục) và sắp xếp theo thời gian
    backup_files = [f for f in backup_files if not f.get("IsDir", False)]
    
    if not backup_files:
        print(f"\n❌ No backup files found for {website_name} on {remote_name}")
        input("\nPress Enter to continue...")
        return
    
    # Sort backup files by modification time (newest first)
    backup_files.sort(key=lambda x: x.get("ModTime", ""), reverse=True)
    
    # Prepare a list of backup files with detailed information for display
    backup_choices = []
    backup_files_dict = {}  # Keep a mapping of display string to actual backup file and path
    
    for backup in backup_files:
        name = backup.get("Name", "Unknown")
        path = backup.get("Path", name)  # Get full path if available
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
            from datetime import datetime
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
    print(f"\n📋 Found {len(backup_files)} backup files for {website_name}:")
    
    # Group backups by type
    database_backups = [b for b in backup_files if b.get("Name", "").endswith(".sql")]
    files_backups = [b for b in backup_files if b.get("Name", "").endswith((".tar.gz", ".tgz"))]
    
    if database_backups:
        most_recent_db = database_backups[0]
        db_name = most_recent_db.get("Name", "Unknown")
        db_date = "Unknown"
        try:
            from datetime import datetime
            mod_time = datetime.strptime(most_recent_db.get("ModTime", "").split(".")[0], "%Y-%m-%dT%H:%M:%S")
            db_date = mod_time.strftime("%d/%m/%Y %H:%M:%S")
        except:
            pass
        print(f"   Most recent database backup: {db_name} (created on {db_date})")
    
    if files_backups:
        most_recent_file = files_backups[0]
        file_name = most_recent_file.get("Name", "Unknown")
        file_date = "Unknown"
        try:
            from datetime import datetime
            mod_time = datetime.strptime(most_recent_file.get("ModTime", "").split(".")[0], "%Y-%m-%dT%H:%M:%S")
            file_date = mod_time.strftime("%d/%m/%Y %H:%M:%S")
        except:
            pass
        print(f"   Most recent files backup: {file_name} (created on {file_date})")
    
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
    
    selected_backup_info = backup_files_dict[selected_display]
    selected_backup_name = selected_backup_info["name"]
    selected_backup_path = selected_backup_info["path"]
    
    # Find the full backup information for display in confirmation
    selected_backup_full = next((b for b in backup_files if b.get("Name") == selected_backup_name), None)
    if selected_backup_full:
        # Get the modification time for confirmation message
        modified_str = selected_backup_full.get("ModTime", "Unknown")
        try:
            from datetime import datetime
            mod_time = datetime.strptime(modified_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
            backup_date = mod_time.strftime("%d/%m/%Y %H:%M:%S")
        except:
            backup_date = modified_str
        
        backup_type = "Database" if selected_backup_name.endswith(".sql") else "Files" if selected_backup_name.endswith((".tar.gz", ".tgz")) else "Unknown"
    else:
        backup_date = "Unknown date"
        backup_type = "Unknown type"
    
    # Xác định đường dẫn đầy đủ trên remote
    # Nếu có path và khác name, sử dụng path để tạo đường dẫn đầy đủ
    if selected_backup_path and selected_backup_path != selected_backup_name:
        # Path đã bao gồm phần website_name và thư mục backup
        remote_path = selected_backup_path
    else:
        # Cấu trúc đơn giản, chỉ có file ở root của website_name
        remote_path = f"backups/{website_name}/{selected_backup_name}"
    
    # Confirm restoration with detailed information
    print(f"\n📋 Backup Details:")
    print(f"   Website: {website_name}")
    print(f"   Backup file: {selected_backup_name}")
    print(f"   Type: {backup_type}")
    print(f"   Created: {backup_date}")
    
    # Define standard paths
    sites_dir = get_env_value("SITES_DIR")
    wordpress_dir = os.path.join(sites_dir, website_name, "wordpress")
    
    print(f"   Source: {remote_name}:{remote_path}")
    print(f"   Standard restore path: {wordpress_dir}")
    
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
    print(f"\n📥 Downloading backup file {selected_backup_name}...")
    
    backup_dir = get_env_value("BACKUP_DIR")
    local_path = os.path.join(backup_dir, selected_backup_name)
    
    # Create a temporary directory in the website's directory for the restore process
    temp_dir = os.path.join(sites_dir, website_name, "temp_cloud_restore")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Download backup file to the temporary directory first
    success, message = integration.restore_from_remote(
        remote_name, 
        remote_path, 
        local_path,
        website_name
    )
    
    if not success:
        print(f"\n❌ {message}")
        input("\nPress Enter to continue...")
        return
    
    # Restore website from the downloaded backup
    print(f"\n🔄 Restoring website from backup...")
    
    try:
        # Determine backup type
        is_database = selected_backup.endswith('.sql')
        is_archive = selected_backup.endswith('.tar.gz') or selected_backup.endswith('.tgz')
        
        if is_database:
            # Restore database directly using MySQL module
            from core.backend.modules.mysql.import_export import import_database
            print(f"\n🗃️ Restoring database from {selected_backup}...")
            import_database(website_name, local_path, reset=True)
            restore_success = True
            
        elif is_archive:
            # Restore source code using specialized functions
            from core.backend.modules.backup.backup_restore import restore_source_code
            print(f"\n📦 Extracting WordPress files from {selected_backup}...")
            restore_success = restore_source_code(website_name, local_path)
            
        else:
            print(f"\n❌ Unknown backup file type: {selected_backup}")
            restore_success = False
        
        # If restoration was successful, restart the website
        if restore_success:
            print(f"\n🔄 Restarting website {website_name}...")
            from core.backend.modules.backup.backup_restore import restart_website
            restart_result = restart_website(website_name)
            
            if restart_result:
                print(f"\n✅ Website {website_name} restarted successfully")
            else:
                print(f"\n⚠️ Website restored but could not be restarted automatically")
            
            print(f"\n✅ Website {website_name} restored successfully from cloud backup")
        else:
            print(f"\n❌ Failed to restore website {website_name} from cloud backup")
    
    finally:
        # Clean up temporary directory if it exists
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"\n🧹 Cleaned up temporary files")
            except Exception as e:
                print(f"\n⚠️ Could not clean up temporary directory: {str(e)}")
    
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
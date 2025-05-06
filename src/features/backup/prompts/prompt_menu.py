"""
Backup management menu prompt module.

This module provides the user interface for backup and restore functions
like creating backups, restoring backups, scheduling automatic backups,
and cloud backup integration.
"""

import os
import questionary
from questionary import Style
from typing import Optional, List, Dict, Any

from src.common.logging import info, error, debug, success, warn
from src.common.utils.environment import get_env_value
from src.features.website.utils import select_website, website_list
from src.features.backup.backup_manager import BackupManager
from src.features.backup.website_backup import backup_website

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

def prompt_backup_website() -> None:
    """Prompt to create website backup."""
    try:
        from src.features.backup.prompts.prompt_backup_website import prompt_backup_website as original_prompt
        original_prompt()
    except ImportError:
        info("\n📋 Create Website Backup")
        
        # Get available websites
        websites = select_website()
        
        if not websites:
            error("❌ No websites found")
            input("\nPress Enter to continue...")
            return
            
        # Create website choices
        website_choices = [{"name": website, "value": website} for website in websites]
        website_choices.append({"name": "Cancel", "value": "cancel"})
        
        # Select website
        selected_website = questionary.select(
            "Select website to backup:",
            choices=website_choices,
            style=custom_style
        ).ask()
        
        if selected_website == "cancel":
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
                prompt_cloud_backup_upload(selected_website, backup_path)
        else:
            error("❌ Backup creation failed")
        
        input("\nPress Enter to continue...")


def prompt_restore_backup() -> None:
    """Prompt to restore website backup."""
    info("\n📋 Restore Website Backup")
    
    # Get selected website using the utility function
    selected_website = select_website("Select website to restore:")
    
    if not selected_website:
        info("Operation cancelled or no websites found.")
        input("\nPress Enter to continue...")
        return
    
    # Get backup source
    source_choices = [
        {"name": "Local backup", "value": "local"},
        {"name": "Cloud backup", "value": "cloud"},
        {"name": "Cancel", "value": "cancel"}
    ]
    
    backup_source = questionary.select(
        "Select backup source:",
        choices=source_choices,
        style=custom_style
    ).ask()
    
    if backup_source == "cancel":
        return
    
    if backup_source == "local":
        # Get available local backups
        from src.features.backup.backup_restore import get_backup_folders, get_backup_info
        
        backup_dir, backup_folders, last_backup_info = get_backup_folders(selected_website)
        
        if not backup_folders:
            error(f"❌ No local backups found for website: {selected_website}")
            input("\nPress Enter to continue...")
            return
        
        # Create backup choices
        backup_choices = []
        for folder in backup_folders:
            backup_info = get_backup_info(backup_dir, folder, last_backup_info)
            
            # Prepare display string
            time_str = backup_info.get("time", "Unknown")
            size_str = backup_info.get("size", "Unknown")
            is_latest = backup_info.get("is_latest", False)
            
            choice_str = f"{folder} ({time_str}, {size_str})" + (" [Current]" if is_latest else "")
            backup_choices.append({"name": choice_str, "value": backup_info})
        
        backup_choices.append({"name": "Cancel", "value": "cancel"})
        
        # Select backup
        selected_backup = questionary.select(
            "Select backup to restore:",
            choices=backup_choices,
            style=custom_style
        ).ask()
        
        if selected_backup == "cancel":
            return
        
        # Show detailed information for the selected backup
        info(f"\n📋 Backup Details:")
        info(f"  📁 Folder: {selected_backup['folder']}")
        info(f"  ⏱️  Created: {selected_backup['time']}")
        info(f"  💾 Size: {selected_backup['size']}")
        
        # Check what's available in the backup
        has_database = selected_backup.get("sql_file") is not None
        has_files = selected_backup.get("archive_file") is not None
        
        if has_database:
            info(f"  🗃️ Database backup available")
        
        if has_files:
            info(f"  📦 Files backup available")
        
        if not has_database and not has_files:
            error("❌ No database or files backup found in this backup folder")
            input("\nPress Enter to continue...")
            return
        
        # Choose what to restore
        restore_choices = []
        
        if has_database:
            restore_choices.append({"name": "Database only", "value": "database"})
        
        if has_files:
            restore_choices.append({"name": "Files only", "value": "files"})
        
        if has_database and has_files:
            restore_choices.append({"name": "Both database and files", "value": "both"})
        
        restore_choices.append({"name": "Cancel", "value": "cancel"})
        
        restore_option = questionary.select(
            "What would you like to restore?",
            choices=restore_choices,
            style=custom_style
        ).ask()
        
        if restore_option == "cancel":
            return
        
        # Confirm restoration
        if not questionary.confirm(
            f"Are you sure you want to restore the {restore_option} for {selected_website}?",
            style=custom_style,
            default=False
        ).ask():
            return
        
        # Perform restoration
        from src.features.backup.backup_restore import restore_database, restore_source_code, restart_website
        
        restore_success = True
        
        try:
            if restore_option in ["database", "both"] and has_database:
                info(f"\n🗃️  Restoring database...")
                db_success = restore_database(selected_website, selected_backup["sql_file"])
                
                if db_success:
                    success("✅ Database restored successfully")
                else:
                    error("❌ Database restoration failed")
                    restore_success = False
            
            if restore_option in ["files", "both"] and has_files:
                info(f"\n📦 Restoring website files...")
                files_success = restore_source_code(selected_website, selected_backup["archive_file"])
                
                if files_success:
                    success("✅ Website files restored successfully")
                else:
                    error("❌ Website files restoration failed")
                    restore_success = False
            
            # Restart website if restoration was successful
            if restore_success:
                info(f"\n🔄 Restarting website {selected_website}...")
                restart_success = restart_website(selected_website)
                
                if restart_success:
                    success(f"✅ Website {selected_website} restarted successfully")
                else:
                    warn(f"⚠️ Website restored but could not be restarted automatically")
        except Exception as e:
            error(f"❌ Error during restoration: {str(e)}")
            restore_success = False
        
        # Final result message
        if restore_success:
            success(f"\n✅ Website {selected_website} restored successfully")
        else:
            error(f"\n❌ Website {selected_website} restoration had errors")
    
    else:  # Cloud backup
        from src.features.backup.prompts.prompt_cloud_backup import prompt_restore_from_cloud
        prompt_restore_from_cloud()
    
    input("\nPress Enter to continue...")


def prompt_list_backups() -> None:
    """List available backups."""
    info("\n📋 List Backups")
    
    # Get backup source
    source_choices = [
        {"name": "Local backups", "value": "local"},
        {"name": "Cloud backups", "value": "cloud"},
        {"name": "All backups", "value": "all"},
        {"name": "Cancel", "value": "cancel"}
    ]
    
    backup_source = questionary.select(
        "Select backup source to list:",
        choices=source_choices,
        style=custom_style
    ).ask()
    
    if backup_source == "cancel":
        return
    
    # Get website filter
    all_websites = website_list()
    website_choices = [{"name": "All websites", "value": None}]
    
    if all_websites:
        # Create website selection
        website_choices.extend([{"name": website, "value": website} for website in all_websites])
    
    selected_website = questionary.select(
        "Filter by website:",
        choices=website_choices,
        style=custom_style
    ).ask()
    
    # List backups
    backup_manager = BackupManager()
    
    if backup_source == "local":
        # Only list from local provider
        backups = backup_manager.list_backups(selected_website, "local")
    elif backup_source == "cloud":
        # Only list from cloud providers
        providers = backup_manager.get_available_providers()
        cloud_providers = [p for p in providers if p != "local"]
        
        backups = []
        for provider in cloud_providers:
            provider_backups = backup_manager.list_backups(selected_website, provider)
            backups.extend(provider_backups)
    else:  # All backups
        backups = backup_manager.list_backups(selected_website)
    
    if not backups:
        info("No backups found")
        input("\nPress Enter to continue...")
        return
    
    # Group backups by provider and domain
    grouped_backups: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    
    for backup in backups:
        provider = backup.get("provider", "unknown")
        website = backup.get("website", "unknown")
        
        if provider not in grouped_backups:
            grouped_backups[provider] = {}
        
        if website not in grouped_backups[provider]:
            grouped_backups[provider][website] = []
        
        grouped_backups[provider][website].append(backup)
    
    # Display backups
    for provider_name, websites in grouped_backups.items():
        info(f"\n📂 {provider_name}:")
        
        for website_name, website_backups in websites.items():
            info(f"  📁 {website_name}:")
            
            # Sort by name (most recent first assumes standard naming)
            sorted_backups = sorted(website_backups, key=lambda x: x.get("name", ""), reverse=True)
            
            for i, backup in enumerate(sorted_backups, 1):
                name = backup.get("name", "unknown")
                size = backup.get("size", "unknown")
                modified = backup.get("modified", "unknown")
                modified_str = modified if isinstance(modified, str) else "unknown"
                
                # Classify backup type
                backup_type = "Unknown"
                if name.endswith('.sql'):
                    backup_type = "Database"
                elif name.endswith(('.tar.gz', '.tgz')):
                    backup_type = "Files"
                
                info(f"    {i}. {name} [{backup_type}] - {size} - {modified_str}")
    
    input("\nPress Enter to continue...")


def prompt_delete_backup() -> None:
    """Prompt to delete backup."""
    info("\n🗑️  Delete Backup")
    
    # Get backup source
    source_choices = [
        {"name": "Local backup", "value": "local"},
        {"name": "Cloud backup", "value": "cloud"},
        {"name": "Cancel", "value": "cancel"}
    ]
    
    backup_source = questionary.select(
        "Select backup source:",
        choices=source_choices,
        style=custom_style
    ).ask()
    
    if backup_source == "cancel":
        return
    
    # Get selected website using the utility function
    selected_website = select_website("Select website:")
    
    if not selected_website:
        info("Operation cancelled or no websites found.")
        input("\nPress Enter to continue...")
        return
    
    backup_manager = BackupManager()
    
    if backup_source == "local":
        # List local backups for the selected website
        from src.features.backup.backup_restore import get_backup_folders, get_backup_info
        
        backup_dir, backup_folders, last_backup_info = get_backup_folders(selected_website)
        
        if not backup_folders:
            error(f"❌ No local backups found for website: {selected_website}")
            input("\nPress Enter to continue...")
            return
        
        # Create backup choices
        backup_choices = []
        for folder in backup_folders:
            backup_info = get_backup_info(backup_dir, folder, last_backup_info)
            
            # Prepare display string
            time_str = backup_info.get("time", "Unknown")
            size_str = backup_info.get("size", "Unknown")
            is_latest = backup_info.get("is_latest", False)
            
            choice_str = f"{folder} ({time_str}, {size_str})" + (" [Current]" if is_latest else "")
            backup_choices.append({"name": choice_str, "value": backup_info})
        
        backup_choices.append({"name": "Cancel", "value": "cancel"})
        
        # Select backup
        selected_backup = questionary.select(
            "Select backup to delete:",
            choices=backup_choices,
            style=custom_style
        ).ask()
        
        if selected_backup == "cancel":
            return
        
        # Confirm deletion
        if not questionary.confirm(
            f"Are you sure you want to delete this backup? This action cannot be undone.",
            style=custom_style,
            default=False
        ).ask():
            return
        
        # Delete backup folder
        import shutil
        try:
            folder_path = selected_backup.get("path")
            if folder_path and os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                success(f"✅ Backup deleted successfully")
            else:
                error(f"❌ Backup folder not found: {folder_path}")
        except Exception as e:
            error(f"❌ Error deleting backup: {str(e)}")
    
    else:  # Cloud backup
        # List cloud providers
        providers = backup_manager.get_available_providers()
        cloud_providers = [p for p in providers if p != "local"]
        
        if not cloud_providers:
            error("❌ No cloud storage providers found")
            input("\nPress Enter to continue...")
            return
        
        # Create provider choices
        provider_choices = [{"name": p, "value": p} for p in cloud_providers]
        provider_choices.append({"name": "Cancel", "value": "cancel"})
        
        # Select provider
        selected_provider = questionary.select(
            "Select cloud provider:",
            choices=provider_choices,
            style=custom_style
        ).ask()
        
        if selected_provider == "cancel":
            return
        
        # List backups from the selected provider
        backups = backup_manager.list_backups(selected_website, selected_provider)
        
        if not backups:
            error(f"❌ No backups found for website: {selected_website} on provider: {selected_provider}")
            input("\nPress Enter to continue...")
            return
        
        # Create backup choices
        backup_choices = []
        for backup in backups:
            name = backup.get("name", "unknown")
            size = backup.get("size", "unknown")
            modified = backup.get("modified", "unknown")
            
            # Classify backup type
            backup_type = "Unknown"
            if name.endswith('.sql'):
                backup_type = "Database"
            elif name.endswith(('.tar.gz', '.tgz')):
                backup_type = "Files"
            
            choice_str = f"{name} [{backup_type}] - {size} - {modified}"
            backup_choices.append({"name": choice_str, "value": backup})
        
        backup_choices.append({"name": "Cancel", "value": "cancel"})
        
        # Select backup
        selected_backup = questionary.select(
            "Select backup to delete:",
            choices=backup_choices,
            style=custom_style
        ).ask()
        
        if selected_backup == "cancel":
            return
        
        # Confirm deletion
        if not questionary.confirm(
            f"Are you sure you want to delete this backup from cloud storage? This action cannot be undone.",
            style=custom_style,
            default=False
        ).ask():
            return
        
        # Delete backup
        success_result, message = backup_manager.delete_backup(
            selected_website,
            selected_backup.get("name", ""),
            selected_provider
        )
        
        if success_result:
            success(f"✅ {message}")
        else:
            error(f"❌ {message}")
    
    input("\nPress Enter to continue...")


def prompt_schedule_backup() -> None:
    """Prompt to schedule automatic backups."""
    info("\n🕒 Schedule Automatic Backup")
    
    # Get selected website using the utility function
    selected_website = select_website("Select website to schedule backups for:")
    
    if not selected_website:
        info("Operation cancelled or no websites found.")
        input("\nPress Enter to continue...")
        return
    
    # Get backup options
    backup_options = [
        {"name": "Enable scheduled backups", "value": "enable"},
        {"name": "Disable scheduled backups", "value": "disable"},
        {"name": "Cancel", "value": "cancel"}
    ]
    
    backup_option = questionary.select(
        "Select action:",
        choices=backup_options,
        style=custom_style
    ).ask()
    
    if backup_option == "cancel":
        return
    
    # Schedule configuration
    schedule = {
        "enabled": backup_option == "enable"
    }
    
    if backup_option == "enable":
        # Select storage provider
        backup_manager = BackupManager()
        providers = backup_manager.get_available_providers()
        
        provider_choices = [{"name": p, "value": p} for p in providers]
        provider_choices.append({"name": "Cancel", "value": "cancel"})
        
        selected_provider = questionary.select(
            "Select storage provider for backups:",
            choices=provider_choices,
            style=custom_style
        ).ask()
        
        if selected_provider == "cancel":
            return
        
        # Select schedule type
        schedule_types = [
            {"name": "Daily", "value": "daily"},
            {"name": "Weekly", "value": "weekly"},
            {"name": "Monthly", "value": "monthly"},
            {"name": "Cancel", "value": "cancel"}
        ]
        
        schedule_type = questionary.select(
            "Select schedule type:",
            choices=schedule_types,
            style=custom_style
        ).ask()
        
        if schedule_type == "cancel":
            return
        
        schedule["schedule_type"] = schedule_type
        
        # Set time
        hour = questionary.select(
            "Select hour (24-hour format):",
            choices=[{"name": str(h), "value": h} for h in range(24)],
            style=custom_style
        ).ask()
        
        minute = questionary.select(
            "Select minute:",
            choices=[{"name": str(m).zfill(2), "value": m} for m in [0, 15, 30, 45]],
            style=custom_style
        ).ask()
        
        schedule["hour"] = hour
        schedule["minute"] = minute
        
        # Additional options based on schedule type
        if schedule_type == "weekly":
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_choices = [{"name": day, "value": i} for i, day in enumerate(days)]
            
            day_of_week = questionary.select(
                "Select day of week:",
                choices=day_choices,
                style=custom_style
            ).ask()
            
            schedule["day_of_week"] = day_of_week
        
        elif schedule_type == "monthly":
            day_choices = [{"name": str(d), "value": d} for d in range(1, 29)]
            day_choices.append({"name": "Last day of month", "value": 28})
            
            day_of_month = questionary.select(
                "Select day of month:",
                choices=day_choices,
                style=custom_style
            ).ask()
            
            schedule["day_of_month"] = day_of_month
        
        # Retention count
        retention_count = questionary.select(
            "Select how many backups to keep:",
            choices=[{"name": str(n), "value": n} for n in [1, 3, 5, 10, 15, 30]],
            style=custom_style
        ).ask()
        
        schedule["retention_count"] = retention_count
        
        # Display schedule summary
        info(f"\n📋 Backup Schedule Summary:")
        info(f"  Website: {selected_website}")
        info(f"  Storage: {selected_provider}")
        info(f"  Schedule: {schedule_type.capitalize()}")
        info(f"  Time: {hour}:{str(minute).zfill(2)}")
        
        if schedule_type == "weekly":
            info(f"  Day: {days[day_of_week]}")
        elif schedule_type == "monthly":
            info(f"  Day of month: {day_of_month}")
        
        info(f"  Keep last {retention_count} backups")
        
        # Confirm schedule
        if not questionary.confirm(
            "Do you want to apply this backup schedule?",
            style=custom_style,
            default=True
        ).ask():
            return
        
        # Apply schedule
        success_result, message = backup_manager.schedule_backup(
            selected_website,
            schedule,
            selected_provider
        )
    else:  # Disable backups
        # Create schedule with enabled=False
        schedule = {"enabled": False}
        
        # Apply schedule - use local provider as it doesn't matter for disabling
        backup_manager = BackupManager()
        success_result, message = backup_manager.schedule_backup(selected_website, schedule, "local")
    
    # Show result
    if success_result:
        success(f"✅ {message}")
    else:
        error(f"❌ {message}")
    
    input("\nPress Enter to continue...")


def prompt_cloud_backup_upload(domain: Optional[str] = None, backup_path: Optional[str] = None) -> None:
    """Handle uploading backup to cloud storage."""
    info("\n☁️  Upload Backup to Cloud Storage")
    
    # Import here to avoid circular imports
    from src.features.rclone.manager import RcloneManager
    
    # Check if Rclone is available
    rclone_manager = RcloneManager()
    remotes = rclone_manager.list_remotes()
    
    if not remotes:
        error("❌ No Rclone remotes configured. Please add a remote in the Rclone management menu first.")
        input("\nPress Enter to continue...")
        return
    
    # If domain not provided, select website
    if not domain:
        domain = select_website("Select website:")
        
        if not domain:
            info("Operation cancelled or no websites found.")
            input("\nPress Enter to continue...")
            return
    
    # If backup_path not provided, find backup files
    if not backup_path:
        # Get site directory
        sites_dir = get_env_value("SITES_DIR")
        backup_dir = os.path.join(sites_dir, domain, "backups")
        
        if not os.path.exists(backup_dir):
            error(f"❌ No backup directory found for website: {domain}")
            input("\nPress Enter to continue...")
            return
        
        # Find backup files
        backup_files = []
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                if file.endswith(".sql") or file.endswith(".tar.gz") or file.endswith(".tgz"):
                    full_path = os.path.join(root, file)
                    mtime = os.path.getmtime(full_path)
                    size = os.path.getsize(full_path)
                    size_str = "";
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.2f} KB"
                    elif size < 1024 * 1024 * 1024:
                        size_str = f"{size / (1024 * 1024):.2f} MB"
                    else:
                        size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"
                    
                    backup_files.append({
                        "path": full_path,
                        "name": file,
                        "time": mtime,
                        "size": size_str
                    })
        
        if not backup_files:
            error(f"❌ No backup files found for website: {domain}")
            input("\nPress Enter to continue...")
            return
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x["time"], reverse=True)
        
        # Create backup choices
        backup_choices = []
        for backup in backup_files:
            import datetime
            time_str = datetime.datetime.fromtimestamp(backup["time"]).strftime("%Y-%m-%d %H:%M:%S")
            choice_str = f"{backup['name']} ({time_str}, {backup['size']})"
            backup_choices.append({"name": choice_str, "value": backup["path"]})
        
        backup_choices.append({"name": "Cancel", "value": "cancel"})
        
        # Select backup
        backup_path = questionary.select(
            "Select backup file to upload:",
            choices=backup_choices,
            style=custom_style
        ).ask()
        
        if backup_path == "cancel":
            return
    
    # Select remote
    remote_choices = [{"name": remote, "value": remote} for remote in remotes]
    remote_choices.append({"name": "Cancel", "value": "cancel"})
    
    selected_remote = questionary.select(
        "Select destination remote:",
        choices=remote_choices,
        style=custom_style
    ).ask()
    
    if selected_remote == "cancel":
        return
    
    # Upload backup to cloud
    from src.features.rclone.backup_integration import RcloneBackupIntegration
    
    info(f"\n☁️  Uploading backup to {selected_remote}...")
    
    integration = RcloneBackupIntegration()
    success_result, message = integration.backup_to_remote(
        selected_remote, 
        domain,
        backup_path
    )
    
    if success_result:
        success(f"✅ {message}")
    else:
        error(f"❌ {message}")
    
    input("\nPress Enter to continue...")


def prompt_backup_menu() -> None:
    """Display backup management menu and handle user selection."""
    try:
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
        
        if answer == "0":
            return
        elif answer == "1":
            prompt_backup_website()
        elif answer == "2":
            prompt_restore_backup()
        elif answer == "3":
            prompt_list_backups()
        elif answer == "4":
            prompt_delete_backup()
        elif answer == "5":
            prompt_schedule_backup()
        elif answer == "6":
            prompt_cloud_backup()
    except Exception as e:
        error(f"Error in backup menu: {e}")
        input("Press Enter to continue...")
"""
CLI implementation for backup operations.

This module contains functions to handle backup creation and cloud backup operations.
"""

from typing import List, Optional, Dict, Any, Tuple

from src.common.logging import log_call, info, error, success, debug
from src.features.backup.backup_manager import BackupManager
from src.features.backup.website_backup import backup_website
from src.features.rclone.manager import RcloneManager
from src.features.website.utils import get_site_config


@log_call
def create_website_backup(domain: str) -> Tuple[bool, str]:
    """
    Create a backup for a website.
    
    Args:
        domain: Website domain
        
    Returns:
        Tuple with success status and message/path
    """
    try:
        info(f"🚀 Creating backup for website: {domain}")
        
        # Check if website exists
        site_config = get_site_config(domain)
        if not site_config:
            return False, f"Website configuration not found for domain: {domain}"
        
        # Perform the backup
        backup_path = backup_website(domain)
        
        if not backup_path:
            return False, f"Backup failed for website: {domain}"
        
        return True, backup_path
    except Exception as e:
        error(f"Error in create_website_backup: {str(e)}")
        return False, f"Backup failed: {str(e)}"


@log_call
def backup_to_cloud(domain: str, backup_path: str, remote: str) -> Tuple[bool, str]:
    """
    Upload a backup file to cloud storage.
    
    Args:
        domain: Website domain
        backup_path: Path to backup file
        remote: Name of rclone remote
        
    Returns:
        Tuple with success status and message
    """
    try:
        # Check if remote exists
        rclone_manager = RcloneManager()
        remotes = rclone_manager.list_remotes()
        
        if remote not in remotes:
            return False, f"Remote '{remote}' not found. Available remotes: {', '.join(remotes)}"
        
        # Check if backup file exists
        if not backup_path:
            return False, "Backup path is empty"
        
        from src.features.rclone.backup_integration import RcloneBackupIntegration
        backup_integration = RcloneBackupIntegration()
        
        # Upload backup to remote
        info(f"☁️ Uploading backup to remote storage: {remote}")
        success_result, message = backup_integration.backup_to_remote(
            remote, domain, backup_path
        )
        
        return success_result, message
    except Exception as e:
        error(f"Error in backup_to_cloud: {str(e)}")
        return False, f"Upload to cloud failed: {str(e)}"


@log_call
def list_cloud_backups(domain: Optional[str] = None, remote: Optional[str] = None) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    List backups available on cloud storage.
    
    Args:
        domain: Optional website domain filter
        remote: Optional remote name filter
        
    Returns:
        Tuple with success status and list of backups
    """
    try:
        rclone_manager = RcloneManager()
        
        # If remote is specified, check if it exists
        if remote:
            remotes = rclone_manager.list_remotes()
            if remote not in remotes:
                return False, []
        
        from src.features.rclone.backup_integration import RcloneBackupIntegration
        backup_integration = RcloneBackupIntegration()
        
        # List remote backups
        if remote:
            info(f"🔍 Listing backups from remote: {remote}")
            backups = backup_integration.list_remote_backups(remote, domain)
        else:
            info("🔍 Listing backups from all remotes")
            backups = []
            for r in rclone_manager.list_remotes():
                remote_backups = backup_integration.list_remote_backups(r, domain)
                for backup in remote_backups:
                    backup["remote"] = r
                backups.extend(remote_backups)
        
        return True, backups
    except Exception as e:
        error(f"Error in list_cloud_backups: {str(e)}")
        return False, []


@log_call
def restore_from_cloud(domain: str, remote: str, backup_path: str, local_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Restore a backup from cloud storage.
    
    Args:
        domain: Website domain
        remote: Remote name
        backup_path: Path to backup file on remote
        local_path: Optional path to save the file locally
        
    Returns:
        Tuple with success status and message
    """
    try:
        # Check if remote exists
        rclone_manager = RcloneManager()
        remotes = rclone_manager.list_remotes()
        
        if remote not in remotes:
            return False, f"Remote '{remote}' not found. Available remotes: {', '.join(remotes)}"
        
        from src.features.rclone.backup_integration import RcloneBackupIntegration
        backup_integration = RcloneBackupIntegration()
        
        # Download the backup
        info(f"📥 Downloading backup from remote: {remote}")
        success_result, message = backup_integration.restore_from_remote(
            remote, backup_path, local_path, domain
        )
        
        if not success_result:
            return False, message
        
        # If it's a database backup, restore it
        if backup_path.endswith('.sql'):
            from src.features.backup.backup_restore import restore_database
            info(f"🗃️ Restoring database for website: {domain}")
            restore_success = restore_database(domain, local_path)
            
            if not restore_success:
                return False, "Database restoration failed"
        
        # If it's a source code backup, restore it
        elif backup_path.endswith('.tar.gz') or backup_path.endswith('.tgz'):
            from src.features.backup.backup_restore import restore_source_code
            info(f"📦 Restoring website files for website: {domain}")
            restore_success = restore_source_code(domain, local_path)
            
            if not restore_success:
                return False, "Website file restoration failed"
        
        # Restart the website
        from src.features.backup.backup_restore import restart_website
        restart_success = restart_website(domain)
        
        if restart_success:
            success(f"✅ Website {domain} restarted successfully")
        else:
            info(f"⚠️ Website {domain} restored but could not be restarted automatically")
        
        return True, f"Website {domain} restored successfully from cloud backup"
    except Exception as e:
        error(f"Error in restore_from_cloud: {str(e)}")
        return False, f"Restoration from cloud failed: {str(e)}"
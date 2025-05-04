#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from core.backend.modules.rclone.rclone_manager import RcloneManager
from core.backend.modules.rclone.utils import get_backup_filename
from core.backend.utils.container_utils import convert_host_path_to_container
from core.backend.utils.env_utils import get_env_value
from core.backend.utils.debug import Debug


class RcloneBackupIntegration:
    """Integrates Rclone with the backup system."""
    
    def __init__(self):
        """Initialize the backup integration."""
        self.debug = Debug("RcloneBackupIntegration")
        self.rclone_manager = RcloneManager()
        self.backup_dir = get_env_value("BACKUP_DIR")
        
    def backup_to_remote(self, remote_name: str, website_name: str, backup_path: str) -> Tuple[bool, str]:
        """Back up a website to a remote storage.
        
        Args:
            remote_name: The name of the remote to back up to
            website_name: The name of the website to back up
            backup_path: The path to the backup file
            
        Returns:
            A tuple of (success, message)
        """
        if not self.rclone_manager.is_container_running():
            if not self.rclone_manager.start_container():
                return False, "Failed to start Rclone container"
                
        # Create remote destination path
        remote_path = f"backups/{website_name}"
        
        # Ensure backup file exists
        if not os.path.exists(backup_path):
            return False, f"Backup file not found: {backup_path}"
            
        # Get just the filename portion
        backup_filename = os.path.basename(backup_path)
        
        # Execute the backup
        self.debug.info(f"Backing up {backup_path} to {remote_name}:{remote_path}/{backup_filename}")
        
        # Create remote directory first to avoid "directory not found" error
        # Rclone mkdir doesn't support -p, so we'll break it into components
        remote_components = remote_path.split('/')
        current_path = ""
        
        for component in remote_components:
            if component:
                current_path = f"{current_path}/{component}" if current_path else component
                mkdir_success, mkdir_message = self.rclone_manager.execute_command(
                    ["mkdir", f"{remote_name}:{current_path}"]
                )
                # Don't show a warning if the directory already exists
                if not mkdir_success and "already exists" not in mkdir_message.lower():
                    self.debug.warn(f"Unable to create directory '{current_path}': {mkdir_message}")
        
        # Convert the host path to container path for Rclone
        container_backup_path = convert_host_path_to_container(backup_path)
        self.debug.info(f"Container path: {container_backup_path}")
        
        # Use copy instead of sync for single file backup
        success, message = self.rclone_manager.execute_command(
            ["copy", container_backup_path, f"{remote_name}:{remote_path}/{backup_filename}", "--progress"]
        )
        
        if success:
            return True, f"Backup successfully uploaded to {remote_name}:{remote_path}/{backup_filename}"
        else:
            return False, f"Backup failed: {message}"
    
    def list_remote_backups(self, remote_name: str, website_name: Optional[str] = None) -> List[Dict]:
        """List backups on a remote storage.
        
        Args:
            remote_name: The name of the remote to list backups from
            website_name: Optional website name to filter backups
            
        Returns:
            List of backup files information
        """
        if not self.rclone_manager.is_container_running():
            if not self.rclone_manager.start_container():
                return []
                
        # Create remote path to list
        remote_path = "backups"
        if website_name:
            remote_path = f"{remote_path}/{website_name}"
            
        # List files in the remote path
        files = self.rclone_manager.list_files(remote_name, remote_path)
        
        return files
    
    def restore_from_remote(self, remote_name: str, remote_path: str, local_path: str) -> Tuple[bool, str]:
        """Restore a backup from a remote storage.
        
        Args:
            remote_name: The name of the remote to restore from
            remote_path: The path to the backup on the remote
            local_path: The local path to restore to
            
        Returns:
            A tuple of (success, message)
        """
        if not self.rclone_manager.is_container_running():
            if not self.rclone_manager.start_container():
                return False, "Failed to start Rclone container"
                
        # Execute the restore
        self.debug.info(f"Restoring from {remote_name}:{remote_path} to {local_path}")
        success, message = self.rclone_manager.sync(
            f"{remote_name}:{remote_path}",
            local_path,
            ["--progress"]
        )
        
        if success:
            return True, f"Backup successfully restored from {remote_name}:{remote_path}"
        else:
            return False, f"Restore failed: {message}"
    
    def schedule_remote_backup(self, remote_name: str, website_name: str, schedule: str) -> Tuple[bool, str]:
        """Schedule a backup to a remote storage.
        
        Args:
            remote_name: The name of the remote to back up to
            website_name: The name of the website to back up
            schedule: The cron schedule expression
            
        Returns:
            A tuple of (success, message)
        """
        try:
            from core.backend.modules.cron.cron_manager import CronManager
            
            cron_manager = CronManager()
            
            # Create a command that will create a backup and then upload it to the remote
            command = f"{get_env_value('SCRIPTS_DIR')}/backup_to_remote.sh {website_name} {remote_name}"
            
            # Add the job to crontab
            job = cron_manager.add_job(
                command=command,
                comment=f"Auto backup {website_name} to {remote_name}",
                schedule=schedule
            )
            
            if job:
                return True, f"Scheduled backup of {website_name} to {remote_name} with schedule: {schedule}"
            else:
                return False, "Failed to schedule backup"
        except ImportError:
            return False, "Cron module not available"
        except Exception as e:
            self.debug.error(f"Failed to schedule backup: {e}")
            return False, f"Failed to schedule backup: {str(e)}"
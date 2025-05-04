"""
Rclone integration with the backup system.

This module provides functionality for backing up and restoring files
using Rclone remote storage services.
"""

import os
import shutil
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.common.containers.path_utils import convert_host_path_to_container
from src.features.rclone.manager import RcloneManager


class RcloneBackupIntegration:
    """Integrates Rclone with the backup system."""
    
    _instance = None
    
    def __new__(cls) -> 'RcloneBackupIntegration':
        """
        Singleton pattern to ensure only one instance exists.
        
        Returns:
            RcloneBackupIntegration: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(RcloneBackupIntegration, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the backup integration."""
        if self._initialized:
            return
            
        self._initialized = True
        self.debug = Debug("RcloneBackupIntegration")
        self.rclone_manager = RcloneManager()
        self.sites_dir = env["SITES_DIR"]
        
    @log_call
    def backup_to_remote(self, remote_name: str, website_name: str, backup_path: str) -> Tuple[bool, str]:
        """
        Back up a website to a remote storage.
        
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
        container_backup_path = convert_host_path_to_container(backup_path, 'rclone')
        self.debug.info(f"Container path: {container_backup_path}")
        
        # Use copyto instead of copy for more precise file operations
        success, message = self.rclone_manager.execute_command(
            ["copyto", container_backup_path, f"{remote_name}:{remote_path}/{backup_filename}", "--progress"]
        )
        
        if success:
            return True, f"Backup successfully uploaded to {remote_name}:{remote_path}/{backup_filename}"
        else:
            return False, f"Backup failed: {message}"
    
    @log_call
    def list_remote_backups(self, remote_name: str, website_name: Optional[str] = None) -> List[Dict]:
        """
        List backups on a remote storage.
        
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
    
    @log_call
    def restore_from_remote(self, remote_name: str, remote_path: str, local_path: str, 
                          website_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Restore a backup from a remote storage.
        
        Args:
            remote_name: The name of the remote to restore from
            remote_path: The path to the backup on the remote
            local_path: The local path to restore to
            website_name: Optional website name for creating temp directory
            
        Returns:
            A tuple of (success, message)
        """
        if not self.rclone_manager.is_container_running():
            if not self.rclone_manager.start_container():
                return False, "Failed to start Rclone container"
        
        # Create a temporary directory for download if website_name is provided
        temp_dir = None
        actual_local_path = local_path
        
        if website_name:
            if self.sites_dir:
                # Create a temporary directory for this download
                temp_dir = os.path.join(self.sites_dir, website_name, "temp_cloud_restore")
                os.makedirs(temp_dir, exist_ok=True)
                
                # Get just the filename portion more reliably
                # Check if remote_path is a full path
                self.debug.debug(f"Analyzing remote path: {remote_path}")
                
                # Determine filename based on remote path
                path_parts = remote_path.split("/")
                if len(path_parts) > 0:
                    # Get the last part of the path
                    backup_filename = path_parts[-1]
                    
                    # Check if the last part is a valid filename
                    if not any(backup_filename.endswith(ext) for ext in ['.sql', '.tar.gz', '.tgz', '.zip']):
                        # If not a valid filename, use filename from local_path
                        self.debug.warn(f"Remote path does not end with a valid file extension: {backup_filename}")
                        backup_filename = os.path.basename(local_path)
                else:
                    # Cannot parse path, use local_path
                    backup_filename = os.path.basename(local_path)
                
                # Make sure we have a valid filename
                if not backup_filename or backup_filename == "":
                    backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    self.debug.warn(f"Could not determine backup filename, using generated name: {backup_filename}")
                    
                # Log for debugging
                self.debug.info(f"Using backup filename: {backup_filename} from remote path: {remote_path}")
                
                # Set the actual local path to the temporary directory
                actual_local_path = os.path.join(temp_dir, backup_filename)
                self.debug.info(f"Using temporary download path: {actual_local_path}")
        
        # Make sure the target directory exists
        os.makedirs(os.path.dirname(actual_local_path), exist_ok=True)
        
        # Remove the destination if it already exists
        if os.path.exists(actual_local_path):
            try:
                if os.path.isdir(actual_local_path):
                    self.debug.warn(f"Destination path exists as a directory, removing it: {actual_local_path}")
                    shutil.rmtree(actual_local_path)
                else:
                    self.debug.warn(f"Destination file already exists, removing it: {actual_local_path}")
                    os.remove(actual_local_path)
            except Exception as e:
                self.debug.error(f"Error removing existing destination: {str(e)}")
                return False, f"Error removing existing destination: {str(e)}"
        
        # Check if file exists on remote
        check_success, check_output = self.rclone_manager.execute_command(
            ["lsf", f"{remote_name}:{remote_path}"]
        )
        
        if not check_success or not check_output.strip():
            self.debug.error(f"Source file does not exist on remote: {remote_name}:{remote_path}")
            return False, f"Source file does not exist on remote: {remote_name}:{remote_path}"
        
        # Ensure the path doesn't have a trailing / to avoid Rclone misinterpreting it
        remote_path = remote_path.rstrip('/')
        
        # Use size to check information about size without downloading the file
        size_check, size_output = self.rclone_manager.execute_command(
            ["size", f"{remote_name}:{remote_path}"]
        )
        
        if size_check:
            self.debug.info(f"Remote file info: {size_output.strip()}")
        
        # Convert host path to container path for Rclone
        container_local_path = convert_host_path_to_container(actual_local_path, 'rclone')
        
        # Execute the restore using copyto for more precise file operations
        self.debug.info(f"Downloading from {remote_name}:{remote_path} to {actual_local_path}")
        self.debug.info(f"Container path: {container_local_path}")
        
        # Use copyto instead of copy to ensure we're copying a file, not a directory
        success, message = self.rclone_manager.execute_command(
            ["copyto", f"{remote_name}:{remote_path}", container_local_path, "--progress"]
        )
        
        if success:
            # Verify that the file was actually downloaded and is valid
            if not os.path.exists(actual_local_path):
                self.debug.error(f"Download completed but file does not exist: {actual_local_path}")
                return False, f"Download completed but file does not exist: {actual_local_path}"
                
            if os.path.isdir(actual_local_path):
                self.debug.error(f"Download resulted in a directory instead of a file: {actual_local_path}")
                return False, f"Download resulted in a directory instead of a file: {actual_local_path}"
                
            if os.path.getsize(actual_local_path) == 0:
                self.debug.error(f"Downloaded file is empty: {actual_local_path}")
                return False, f"Downloaded file is empty: {actual_local_path}"
            
            # Move the file from temporary location to the actual destination if needed
            if temp_dir and os.path.exists(actual_local_path) and actual_local_path != local_path:
                try:
                    # Create the target directory if it doesn't exist
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    
                    # Remove destination file if it exists
                    if os.path.exists(local_path):
                        if os.path.isdir(local_path):
                            shutil.rmtree(local_path)
                        else:
                            os.remove(local_path)
                    
                    # Copy the file to the actual destination
                    shutil.copy2(actual_local_path, local_path)
                    self.debug.info(f"Copied from temporary location {actual_local_path} to {local_path}")
                    
                    # Verify the copy succeeded
                    if not os.path.exists(local_path) or os.path.isdir(local_path):
                        self.debug.error(f"Failed to copy file to final destination: {local_path}")
                        return False, f"Failed to copy file to final destination: {local_path}"
                    
                    # Don't remove the temp directory yet - it will be cleaned up after the restore process
                except Exception as e:
                    self.debug.error(f"Error copying from temporary location: {str(e)}")
                    return False, f"Error copying from temporary location: {str(e)}"
            
            return True, f"Backup successfully downloaded from {remote_name}:{remote_path}"
        else:
            # Clean up the temporary directory if it was created
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    self.debug.warn(f"Failed to remove temporary directory: {str(e)}")
            
            return False, f"Download failed: {message}"
    
    @log_call
    def schedule_remote_backup(self, remote_name: str, website_name: str, schedule: str) -> Tuple[bool, str]:
        """
        Schedule a backup to a remote storage.
        
        Args:
            remote_name: The name of the remote to back up to
            website_name: The name of the website to back up
            schedule: The cron schedule expression
            
        Returns:
            A tuple of (success, message)
        """
        try:
            from src.features.cron.manager import CronManager
            
            cron_manager = CronManager()
            
            # Create a command that will create a backup and then upload it to the remote
            command = f"{env['SCRIPTS_DIR']}/backup_to_remote.sh {website_name} {remote_name}"
            
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
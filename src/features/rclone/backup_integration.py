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
        # Validate inputs
        if not remote_name or not remote_name.strip():
            self.debug.error("Remote name cannot be empty")
            return False, "Remote name cannot be empty"
            
        if not website_name or not website_name.strip():
            self.debug.error("Website name cannot be empty")
            return False, "Website name cannot be empty"
            
        if not backup_path or not backup_path.strip():
            self.debug.error("Backup path cannot be empty")
            return False, "Backup path cannot be empty"
        
        # Check if the remote exists
        remotes = self.rclone_manager.list_remotes()
        if remote_name not in remotes:
            self.debug.error(f"Remote '{remote_name}' does not exist")
            return False, f"Remote '{remote_name}' does not exist"
        
        # Check if Rclone container is running
        if not self.rclone_manager.is_container_running():
            self.debug.info("Rclone container not running, attempting to start")
            if not self.rclone_manager.start_container():
                self.debug.error("Failed to start Rclone container")
                return False, "Failed to start Rclone container"
                
        # Create remote destination path
        remote_path = f"backups/{website_name}"
        self.debug.info(f"Remote path: {remote_path}")
        
        # Ensure backup file exists and is valid
        try:
            if not os.path.exists(backup_path):
                self.debug.error(f"Backup file not found: {backup_path}")
                return False, f"Backup file not found: {backup_path}"
                
            if os.path.isdir(backup_path):
                self.debug.error(f"Backup path is a directory, not a file: {backup_path}")
                return False, f"Backup path is a directory, not a file: {backup_path}"
                
            if os.path.getsize(backup_path) == 0:
                self.debug.error(f"Backup file is empty: {backup_path}")
                return False, f"Backup file is empty: {backup_path}"
                
            # Validate file extension
            valid_extensions = ['.sql', '.zip', '.tar.gz', '.tgz', '.gz']
            if not any(backup_path.endswith(ext) for ext in valid_extensions):
                self.debug.warn(f"Backup file does not have a standard extension: {backup_path}")
                # Warning only, don't fail
        except Exception as e:
            self.debug.error(f"Error validating backup file: {str(e)}")
            return False, f"Error validating backup file: {str(e)}"
            
        # Get just the filename portion
        backup_filename = os.path.basename(backup_path)
        
        # Execute the backup
        self.debug.info(f"Backing up {backup_path} to {remote_name}:{remote_path}/{backup_filename}")
        
        try:
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
            
            # Verify the container path
            if not container_backup_path or container_backup_path == backup_path:
                self.debug.warn(f"Path conversion may have failed, container path: {container_backup_path}")
            
            # Use copyto instead of copy for more precise file operations
            success, message = self.rclone_manager.execute_command(
                ["copyto", container_backup_path, f"{remote_name}:{remote_path}/{backup_filename}", "--progress"]
            )
            
            if success:
                # Verify the upload by listing the remote directory
                list_success, list_output = self.rclone_manager.execute_command(
                    ["lsf", f"{remote_name}:{remote_path}/{backup_filename}"]
                )
                
                if list_success and list_output.strip():
                    self.debug.info(f"Backup file verified on remote: {remote_name}:{remote_path}/{backup_filename}")
                    return True, f"Backup successfully uploaded to {remote_name}:{remote_path}/{backup_filename}"
                else:
                    self.debug.warn(f"Upload reported success but file verification failed")
                    return True, f"Backup upload completed, but file verification couldn't confirm the upload"
            else:
                self.debug.error(f"Backup upload failed: {message}")
                return False, f"Backup failed: {message}"
                
        except Exception as e:
            self.debug.error(f"Unexpected error during backup: {str(e)}")
            return False, f"Unexpected error during backup: {str(e)}"
    
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
        
        # Only append website_name if it's not None and not an empty string
        if website_name and website_name.strip():
            remote_path = f"{remote_path}/{website_name}"
        elif website_name == "":
            # If empty string is provided, set to None to list all websites
            website_name = None
            
        # List files in the remote path
        try:
            files = self.rclone_manager.list_files(remote_name, remote_path)
            return files
        except Exception as e:
            self.debug.error(f"Error listing files from {remote_name}:{remote_path}: {str(e)}")
            return []
    
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
        # Validate inputs
        if not remote_name or not remote_name.strip():
            self.debug.error("Remote name cannot be empty")
            return False, "Remote name cannot be empty"
            
        if not remote_path or not remote_path.strip():
            self.debug.error("Remote path cannot be empty")
            return False, "Remote path cannot be empty"
            
        if not local_path or not local_path.strip():
            self.debug.error("Local path cannot be empty")
            return False, "Local path cannot be empty"
        
        # Check if the remote exists
        remotes = self.rclone_manager.list_remotes()
        if remote_name not in remotes:
            self.debug.error(f"Remote '{remote_name}' does not exist")
            return False, f"Remote '{remote_name}' does not exist"
        
        # Check if Rclone container is running
        if not self.rclone_manager.is_container_running():
            self.debug.info("Rclone container not running, attempting to start")
            if not self.rclone_manager.start_container():
                self.debug.error("Failed to start Rclone container")
                return False, "Failed to start Rclone container"
        
        # Create a temporary directory for download if website_name is provided
        temp_dir = None
        actual_local_path = local_path
        
        try:
            if website_name:
                if not self.sites_dir:
                    self.debug.warn("SITES_DIR not set, cannot create temporary directory for website")
                else:
                    # Create a temporary directory for this download
                    temp_dir = os.path.join(self.sites_dir, website_name, "temp_cloud_restore")
                    os.makedirs(temp_dir, exist_ok=True)
                    self.debug.info(f"Created temporary directory: {temp_dir}")
                    
                    # Get just the filename portion more reliably
                    # Check if remote_path is a full path
                    self.debug.debug(f"Analyzing remote path: {remote_path}")
                    
                    # Determine filename based on remote path
                    path_parts = remote_path.split("/")
                    if len(path_parts) > 0:
                        # Get the last part of the path
                        backup_filename = path_parts[-1]
                        
                        # Check if the last part is a valid filename
                        valid_extensions = ['.sql', '.tar.gz', '.tgz', '.zip', '.gz']
                        if not any(backup_filename.endswith(ext) for ext in valid_extensions):
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
            try:
                os.makedirs(os.path.dirname(actual_local_path), exist_ok=True)
            except Exception as e:
                self.debug.error(f"Failed to create directory for download: {str(e)}")
                return False, f"Failed to create directory for download: {str(e)}"
            
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
                # Try to parse size information to check if file is empty
                if "objects: 0" in size_output or "total size: 0" in size_output:
                    self.debug.warn("Remote file appears to be empty, proceeding anyway")
            
            # Convert host path to container path for Rclone
            container_local_path = convert_host_path_to_container(actual_local_path, 'rclone')
            
            # Verify the container path
            if not container_local_path or container_local_path == actual_local_path:
                self.debug.warn(f"Path conversion may have failed, container path: {container_local_path}")
            
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
                        if not os.path.exists(local_path):
                            self.debug.error(f"Failed to copy file to final destination: {local_path}")
                            return False, f"Failed to copy file to final destination: {local_path}"
                            
                        if os.path.isdir(local_path):
                            self.debug.error(f"Final destination is a directory, not a file: {local_path}")
                            return False, f"Final destination is a directory, not a file: {local_path}"
                            
                        if os.path.getsize(local_path) == 0:
                            self.debug.error(f"Final destination file is empty: {local_path}")
                            return False, f"Final destination file is empty: {local_path}"
                        
                        self.debug.info(f"File successfully copied to final destination: {local_path}")
                        
                    except Exception as e:
                        self.debug.error(f"Error copying from temporary location: {str(e)}")
                        return False, f"Error copying from temporary location: {str(e)}"
                
                # Report success with the actual destination path
                if actual_local_path != local_path:
                    return True, f"Backup successfully downloaded from {remote_name}:{remote_path} to {local_path}"
                else:
                    return True, f"Backup successfully downloaded from {remote_name}:{remote_path}"
            else:
                self.debug.error(f"Download failed: {message}")
                return False, f"Download failed: {message}"
                
        except Exception as e:
            self.debug.error(f"Unexpected error during restore: {str(e)}")
            return False, f"Unexpected error during restore: {str(e)}"
            
        finally:
            # Clean up the temporary directory if it was created and download failed
            if temp_dir and os.path.exists(temp_dir) and (not success or actual_local_path != local_path):
                try:
                    shutil.rmtree(temp_dir)
                    self.debug.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    self.debug.warn(f"Failed to remove temporary directory: {str(e)}")
                    # Don't fail because of cleanup issue
    
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
        # Validate inputs
        if not remote_name or not remote_name.strip():
            self.debug.error("Remote name cannot be empty")
            return False, "Remote name cannot be empty"
            
        if not website_name or not website_name.strip():
            self.debug.error("Website name cannot be empty")
            return False, "Website name cannot be empty"
            
        if not schedule or not schedule.strip():
            self.debug.error("Schedule cannot be empty")
            return False, "Schedule cannot be empty"
        
        # Check if the remote exists
        remotes = self.rclone_manager.list_remotes()
        if remote_name not in remotes:
            self.debug.error(f"Remote '{remote_name}' does not exist")
            return False, f"Remote '{remote_name}' does not exist"
            
        # Validate schedule format (simple check)
        schedule_parts = schedule.strip().split()
        if len(schedule_parts) != 5:
            self.debug.error(f"Invalid cron schedule format: {schedule}")
            return False, f"Invalid cron schedule format: {schedule}. Expected 5 fields: minute hour day-of-month month day-of-week"
            
        try:
            # Import the CronManager
            try:
                from src.features.cron.manager import CronManager
            except ImportError:
                self.debug.error("Cron module not available")
                return False, "Cron module not available. Cannot schedule backup."
            
            # Get script directory from environment
            scripts_dir = env.get("SCRIPTS_DIR")
            if not scripts_dir:
                self.debug.error("SCRIPTS_DIR environment variable not set")
                return False, "SCRIPTS_DIR environment variable not set. Cannot locate backup script."
                
            # Check if the backup script exists
            backup_script_path = os.path.join(scripts_dir, "backup_to_remote.sh")
            if not os.path.exists(backup_script_path):
                self.debug.error(f"Backup script not found: {backup_script_path}")
                return False, f"Backup script not found: {backup_script_path}"
                
            # Check if the script is executable
            if not os.access(backup_script_path, os.X_OK):
                self.debug.warn(f"Backup script is not executable: {backup_script_path}")
                # This is just a warning, not a failure
                
            # Create the cron manager
            cron_manager = CronManager()
            
            # Create a command that will create a backup and then upload it to the remote
            command = f"{backup_script_path} {website_name} {remote_name}"
            self.debug.info(f"Scheduling command: {command}")
            self.debug.info(f"With schedule: {schedule}")
            
            # Add the job to crontab
            job = cron_manager.add_job(
                command=command,
                comment=f"Auto backup {website_name} to {remote_name}",
                schedule=schedule
            )
            
            if job:
                self.debug.info(f"Successfully scheduled backup job with ID: {job.id}")
                return True, f"Scheduled backup of {website_name} to {remote_name} with schedule: {schedule}"
            else:
                self.debug.error("Failed to schedule backup job")
                return False, "Failed to schedule backup job"
                
        except Exception as e:
            self.debug.error(f"Failed to schedule backup: {str(e)}")
            return False, f"Failed to schedule backup: {str(e)}"
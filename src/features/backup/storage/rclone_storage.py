"""
Rclone-based storage provider for cloud backups.

This module provides a storage provider implementation that uses Rclone
to store backups in cloud storage services.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from src.common.logging import Debug
from src.common.utils.environment import get_env_value
from src.common.containers.path_utils import convert_host_path_to_container
from src.interfaces.IStorageProvider import IStorageProvider


class RcloneStorage(IStorageProvider):
    """Rclone-based storage provider for cloud backups."""
    
    def __init__(self, remote_name: str):
        """
        Initialize the Rclone storage provider.
        
        Args:
            remote_name: Name of the Rclone remote
        """
        self.debug = Debug("RcloneStorage")
        self.remote_name = remote_name
        
        # Import here to avoid circular imports
        from src.features.rclone.manager import RcloneManager
        self.rclone_manager = RcloneManager()
        
        # Base path for backups in the remote
        self.remote_base_path = "backups"
        
        # Temporary directory for downloads
        self.temp_dir = os.path.join(get_env_value("BACKUP_DIR"), "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def store_backup(self, website_name: str, backup_file_path: str) -> Tuple[bool, str]:
        """
        Store a backup file in the cloud storage.
        
        Args:
            website_name: The name of the website
            backup_file_path: Path to the backup file
        
        Returns:
            Tuple of (success, destination_path or error_message)
        """
        try:
            if not self.rclone_manager.is_container_running():
                if not self.rclone_manager.start_container():
                    return False, "Failed to start Rclone container"
            
            # Create remote path for website backups
            remote_path = f"{self.remote_base_path}/{website_name}"
            
            # Get backup filename
            backup_filename = os.path.basename(backup_file_path)
            
            # Full remote destination
            remote_destination = f"{self.remote_name}:{remote_path}/{backup_filename}"
            
            # Create remote directory structure first - rclone mkdir doesn't support -p
            remote_path_components = f"{self.remote_base_path}/{website_name}".split('/')
            current_path = ""
            
            for component in remote_path_components:
                if component:
                    current_path = f"{current_path}/{component}" if current_path else component
                    mkdir_success, mkdir_message = self.rclone_manager.execute_command(
                        ["mkdir", f"{self.remote_name}:{current_path}"]
                    )
                    # Don't show a warning if the directory already exists
                    if not mkdir_success and "already exists" not in mkdir_message.lower():
                        self.debug.warn(f"Unable to create directory '{current_path}': {mkdir_message}")
            
            # Convert host path to container path
            container_backup_path = convert_host_path_to_container(backup_file_path, 'rclone')
            
            # Execute the upload using copyto for more precise file operations
            self.debug.info(f"Uploading {backup_file_path} to {remote_destination}")
            self.debug.info(f"Container path: {container_backup_path}")
            success, message = self.rclone_manager.execute_command(
                ["copyto", container_backup_path, remote_destination, "--progress"]
            )
            
            if success:
                return True, remote_destination
            else:
                return False, f"Failed to upload backup: {message}"
        except Exception as e:
            error_message = f"Failed to store backup: {str(e)}"
            self.debug.error(error_message)
            return False, error_message
    
    def retrieve_backup(self, website_name: str, backup_name: str, destination_path: str) -> Tuple[bool, str]:
        """
        Retrieve a backup file from the cloud storage.
        
        Args:
            website_name: The name of the website
            backup_name: Name of the backup to retrieve
            destination_path: Path where to save the retrieved backup
        
        Returns:
            Tuple of (success, file_path or error_message)
        """
        try:
            if not self.rclone_manager.is_container_running():
                if not self.rclone_manager.start_container():
                    return False, "Failed to start Rclone container"
            
            # Remote path for the backup
            remote_path = f"{self.remote_base_path}/{website_name}/{backup_name}"
            
            # Full remote source
            remote_source = f"{self.remote_name}:{remote_path}"
            
            # Destination container path
            container_destination_path = convert_host_path_to_container(destination_path, 'rclone')
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            
            # Execute the download using copyto for more precise file operations
            self.debug.info(f"Downloading {remote_source} to {destination_path}")
            
            success, message = self.rclone_manager.execute_command(
                ["copyto", remote_source, container_destination_path, "--progress"]
            )
            
            if success:
                return True, destination_path
            else:
                return False, f"Failed to download backup: {message}"
        except Exception as e:
            error_message = f"Failed to retrieve backup: {str(e)}"
            self.debug.error(error_message)
            return False, error_message
    
    def list_backups(self, website_name: Optional[str] = None) -> List[Dict]:
        """
        List available backups in the cloud storage.
        
        Args:
            website_name: Optional filter for website backups
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        try:
            if not self.rclone_manager.is_container_running():
                if not self.rclone_manager.start_container():
                    self.debug.error("Failed to start Rclone container")
                    return backups
            
            # If website_name is provided, only list backups for that website
            if website_name:
                remote_path = f"{self.remote_base_path}/{website_name}"
                self._list_backups_for_website(website_name, remote_path, backups)
            else:
                # First, list all website directories in the backups folder
                website_dirs = self.rclone_manager.list_files(self.remote_name, self.remote_base_path)
                
                # Filter for directories only
                website_dirs = [d for d in website_dirs if d.get("IsDir", False)]
                
                # List backups for each website
                for website_dir in website_dirs:
                    website = website_dir.get("Name")
                    if website:
                        remote_path = f"{self.remote_base_path}/{website}"
                        self._list_backups_for_website(website, remote_path, backups)
            
            # Sort backups by modification time (newest first)
            backups.sort(key=lambda x: x.get("modified", 0), reverse=True)
            
        except Exception as e:
            self.debug.error(f"Error listing backups: {str(e)}")
        
        return backups
    
    def _list_backups_for_website(self, website_name: str, remote_path: str, backups: List[Dict]) -> None:
        """
        Helper method to list backups for a specific website.
        
        Args:
            website_name: The name of the website
            remote_path: Path to the website's backup directory in the remote
            backups: List to append backup information to
        """
        # Get backup files for this website
        backup_files = self.rclone_manager.list_files(self.remote_name, remote_path)
        
        # Filter for non-directories
        backup_files = [f for f in backup_files if not f.get("IsDir", False)]
        
        for backup_file in backup_files:
            try:
                file_name = backup_file.get("Name")
                file_size = backup_file.get("Size", 0)
                mod_time_str = backup_file.get("ModTime", "")
                
                # Parse modification time
                try:
                    mod_time = datetime.strptime(mod_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    try:
                        mod_time = datetime.strptime(mod_time_str, "%Y-%m-%dT%H:%M:%SZ")
                    except ValueError:
                        mod_time = datetime.now()  # Fallback
                
                backups.append({
                    "website": website_name,
                    "name": file_name,
                    "path": f"{remote_path}/{file_name}",
                    "size": file_size,
                    "size_formatted": self._format_size(file_size),
                    "modified": mod_time.timestamp(),
                    "modified_formatted": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "database" if file_name.endswith(".sql") else "full",
                    "provider": f"rclone:{self.remote_name}"
                })
            except Exception as e:
                self.debug.warn(f"Error processing backup file {backup_file.get('Name', 'unknown')}: {str(e)}")
    
    def delete_backup(self, website_name: str, backup_name: str) -> Tuple[bool, str]:
        """
        Delete a backup from the cloud storage.
        
        Args:
            website_name: The name of the website
            backup_name: Name of the backup to delete
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.rclone_manager.is_container_running():
                if not self.rclone_manager.start_container():
                    return False, "Failed to start Rclone container"
            
            # Remote path for the backup
            remote_path = f"{self.remote_base_path}/{website_name}/{backup_name}"
            
            # Full remote source
            remote_source = f"{self.remote_name}:{remote_path}"
            
            # Execute the delete command
            self.debug.info(f"Deleting {remote_source}")
            success, message = self.rclone_manager.execute_command(["delete", remote_source])
            
            if success:
                return True, f"Backup {backup_name} deleted successfully"
            else:
                return False, f"Failed to delete backup: {message}"
        except Exception as e:
            error_message = f"Failed to delete backup: {str(e)}"
            self.debug.error(error_message)
            return False, error_message
    
    def get_provider_name(self) -> str:
        """
        Get the name of this storage provider.
        
        Returns:
            Provider name as string
        """
        return f"rclone:{self.remote_name}"
    
    def _format_size(self, size_bytes: int) -> str:
        """
        Format size in bytes to human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
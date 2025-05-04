"""
Local filesystem storage provider for backups.

This module provides a storage provider implementation that stores backups 
on the local filesystem.
"""

import os
import shutil
import glob
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from src.common.logging import Debug
from src.common.utils.environment import get_env_value
from src.interfaces.IStorageProvider import IStorageProvider


class LocalStorage(IStorageProvider):
    """Local filesystem storage provider for backups."""
    
    def __init__(self):
        """Initialize the local storage provider."""
        self.debug = Debug("LocalStorage")
        self.backup_dir = get_env_value("BACKUP_DIR")
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def store_backup(self, website_name: str, backup_file_path: str) -> Tuple[bool, str]:
        """
        Store a backup file in the local backup directory.
        
        Args:
            website_name: The name of the website
            backup_file_path: Path to the backup file
        
        Returns:
            Tuple of (success, destination_path or error_message)
        """
        try:
            # Create website-specific backup directory if it doesn't exist
            website_backup_dir = os.path.join(self.backup_dir, website_name)
            os.makedirs(website_backup_dir, exist_ok=True)
            
            # Get backup filename
            backup_filename = os.path.basename(backup_file_path)
            
            # Destination path
            destination_path = os.path.join(website_backup_dir, backup_filename)
            
            # Copy the backup file to the destination directory
            if backup_file_path != destination_path:  # Avoid copying to itself
                shutil.copy2(backup_file_path, destination_path)
                self.debug.info(f"Stored backup {backup_filename} for website {website_name}")
            
            return True, destination_path
        except Exception as e:
            error_message = f"Failed to store backup: {str(e)}"
            self.debug.error(error_message)
            return False, error_message
    
    def retrieve_backup(self, website_name: str, backup_name: str, destination_path: str) -> Tuple[bool, str]:
        """
        Retrieve a backup file from the local backup directory.
        
        Args:
            website_name: The name of the website
            backup_name: Name of the backup to retrieve
            destination_path: Path where to save the retrieved backup
        
        Returns:
            Tuple of (success, file_path or error_message)
        """
        try:
            # Website backup directory
            website_backup_dir = os.path.join(self.backup_dir, website_name)
            
            # Source backup path
            source_path = os.path.join(website_backup_dir, backup_name)
            
            # Check if backup exists
            if not os.path.exists(source_path):
                error_message = f"Backup {backup_name} does not exist for website {website_name}"
                self.debug.error(error_message)
                return False, error_message
            
            # Copy the backup file to the destination
            shutil.copy2(source_path, destination_path)
            self.debug.info(f"Retrieved backup {backup_name} for website {website_name}")
            
            return True, destination_path
        except Exception as e:
            error_message = f"Failed to retrieve backup: {str(e)}"
            self.debug.error(error_message)
            return False, error_message
    
    def list_backups(self, website_name: Optional[str] = None) -> List[Dict]:
        """
        List available backups in the local backup directory.
        
        Args:
            website_name: Optional filter for website backups
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        try:
            # If website_name is provided, only list backups for that website
            if website_name:
                website_backup_dir = os.path.join(self.backup_dir, website_name)
                if os.path.exists(website_backup_dir):
                    self._list_backups_for_website(website_name, website_backup_dir, backups)
            else:
                # List backups for all websites
                for website_dir in os.listdir(self.backup_dir):
                    website_backup_dir = os.path.join(self.backup_dir, website_dir)
                    if os.path.isdir(website_backup_dir):
                        self._list_backups_for_website(website_dir, website_backup_dir, backups)
            
            # Sort backups by modification time (newest first)
            backups.sort(key=lambda x: x.get("modified", 0), reverse=True)
            
        except Exception as e:
            self.debug.error(f"Error listing backups: {str(e)}")
        
        return backups
    
    def _list_backups_for_website(self, website_name: str, website_backup_dir: str, backups: List[Dict]) -> None:
        """
        Helper method to list backups for a specific website.
        
        Args:
            website_name: The name of the website
            website_backup_dir: Path to the website's backup directory
            backups: List to append backup information to
        """
        # Find all backup files (tar.gz and sql)
        backup_files = []
        backup_files.extend(glob.glob(os.path.join(website_backup_dir, "*.tar.gz")))
        backup_files.extend(glob.glob(os.path.join(website_backup_dir, "*.sql")))
        
        for backup_file in backup_files:
            try:
                file_name = os.path.basename(backup_file)
                file_size = os.path.getsize(backup_file)
                mod_time = datetime.fromtimestamp(os.path.getmtime(backup_file))
                
                backups.append({
                    "website": website_name,
                    "name": file_name,
                    "path": backup_file,
                    "size": file_size,
                    "size_formatted": self._format_size(file_size),
                    "modified": mod_time.timestamp(),
                    "modified_formatted": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "database" if file_name.endswith(".sql") else "full",
                    "provider": "local"
                })
            except Exception as e:
                self.debug.warn(f"Error processing backup file {backup_file}: {str(e)}")
    
    def delete_backup(self, website_name: str, backup_name: str) -> Tuple[bool, str]:
        """
        Delete a backup from the local backup directory.
        
        Args:
            website_name: The name of the website
            backup_name: Name of the backup to delete
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Website backup directory
            website_backup_dir = os.path.join(self.backup_dir, website_name)
            
            # Backup file path
            backup_path = os.path.join(website_backup_dir, backup_name)
            
            # Check if backup exists
            if not os.path.exists(backup_path):
                error_message = f"Backup {backup_name} does not exist for website {website_name}"
                self.debug.error(error_message)
                return False, error_message
            
            # Delete the backup file
            os.remove(backup_path)
            self.debug.info(f"Deleted backup {backup_name} for website {website_name}")
            
            return True, f"Backup {backup_name} deleted successfully"
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
        return "local"
    
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
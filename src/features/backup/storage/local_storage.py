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
from src.common.utils.validation import validate_directory

class LocalStorage(IStorageProvider):
    """Local filesystem storage provider for backups."""
    
    def __init__(self):
        """Initialize the local storage provider."""
        self.debug = Debug("LocalStorage")
        
        # Get SITES_DIR which is the base for all website directories
        self.sites_dir = get_env_value("SITES_DIR")
        
        if not self.sites_dir:
            # Last resort - use a temporary directory if SITES_DIR is not set
            self.sites_dir = os.path.join("/tmp", "wp_docker_sites")
            self.debug.error(f"SITES_DIR not set, using temporary directory: {self.sites_dir}")
            self.debug.error("Please set SITES_DIR in your environment for proper backup storage")
            
            # Create a central backups directory for this case
            self.backups_dir = os.path.join(self.sites_dir, "backups")
            validate_directory(self.backups_dir, create=True)
        
        self.debug.info(f"Using sites directory: {self.sites_dir}")
    
    def store_backup(self, website_name: str, backup_file_path: str) -> Tuple[bool, str]:
        """
        Store a backup file in the website-specific backups directory.
        
        Args:
            website_name: The name of the website
            backup_file_path: Path to the backup file
        
        Returns:
            Tuple of (success, destination_path or error_message)
        """
        try:
            # Add defensive checks for parameters
            if not website_name:
                error_message = "Website name is empty or None"
                self.debug.error(error_message)
                return False, error_message
                
            if not backup_file_path:
                error_message = "Backup file path is empty or None"
                self.debug.error(error_message)
                return False, error_message
                
            # Log values for debugging
            self.debug.info(f"Storing backup for website '{website_name}'")
            self.debug.info(f"Backup file path: '{backup_file_path}', type: {type(backup_file_path)}")
                
            # Check if backup file exists
            if not os.path.exists(backup_file_path):
                error_message = f"Backup file does not exist: {backup_file_path}"
                self.debug.error(error_message)
                return False, error_message
            
            # Determine the website-specific backup directory (SITES_DIR/website_name/backups)
            if hasattr(self, 'backups_dir'):  # For fallback case when SITES_DIR is not set
                website_backup_dir = os.path.join(self.backups_dir, website_name)
            else:
                website_backup_dir = os.path.join(self.sites_dir, website_name, "backups")
                
            # Create website-specific backup directory if it doesn't exist
            self.debug.info(f"Using website backup directory: {website_backup_dir}")
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
            self.debug.error(f"website_name: {website_name}, backup_file_path: {backup_file_path}")
            return False, error_message
    
    def retrieve_backup(self, website_name: str, backup_name: str, destination_path: str) -> Tuple[bool, str]:
        """
        Retrieve a backup file from the website-specific backups directory.
        
        Args:
            website_name: The name of the website
            backup_name: Name of the backup to retrieve
            destination_path: Path where to save the retrieved backup
        
        Returns:
            Tuple of (success, file_path or error_message)
        """
        try:
            # Determine the website-specific backup directory (SITES_DIR/website_name/backups)
            if hasattr(self, 'backups_dir'):  # For fallback case when SITES_DIR is not set
                website_backup_dir = os.path.join(self.backups_dir, website_name)
            else:
                website_backup_dir = os.path.join(self.sites_dir, website_name, "backups")
            
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
        List available backups for websites.
        
        Args:
            website_name: Optional filter for website backups
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        try:
            # If website_name is provided, only list backups for that website
            if website_name:
                # Determine the website-specific backup directory
                if hasattr(self, 'backups_dir'):  # Fallback case
                    website_backup_dir = os.path.join(self.backups_dir, website_name)
                else:
                    website_backup_dir = os.path.join(self.sites_dir, website_name, "backups")
                
                if os.path.exists(website_backup_dir):
                    self._list_backups_for_website(website_name, website_backup_dir, backups)
                else:
                    self.debug.info(f"Backup directory for website '{website_name}' not found: {website_backup_dir}")
            else:
                # List backups for all websites by scanning SITES_DIR
                if hasattr(self, 'backups_dir'):  # Fallback case
                    # If using the fallback directory, scan it directly
                    for website_dir in os.listdir(self.backups_dir):
                        website_backup_dir = os.path.join(self.backups_dir, website_dir)
                        if os.path.isdir(website_backup_dir):
                            self._list_backups_for_website(website_dir, website_backup_dir, backups)
                else:
                    # Scan SITES_DIR for website directories
                    for website_dir in os.listdir(self.sites_dir):
                        site_path = os.path.join(self.sites_dir, website_dir)
                        if os.path.isdir(site_path):
                            # Check if this site has a backups directory
                            website_backup_dir = os.path.join(site_path, "backups")
                            if os.path.exists(website_backup_dir) and os.path.isdir(website_backup_dir):
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
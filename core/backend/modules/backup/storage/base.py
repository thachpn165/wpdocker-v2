#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Tuple


class StorageProvider(ABC):
    """Abstract base class for backup storage providers."""
    
    @abstractmethod
    def store_backup(self, website_name: str, backup_file_path: str) -> Tuple[bool, str]:
        """Store a backup file.
        
        Args:
            website_name: The name of the website
            backup_file_path: Path to the backup file
        
        Returns:
            Tuple of (success, destination_path or error_message)
        """
        pass
    
    @abstractmethod
    def retrieve_backup(self, website_name: str, backup_name: str, destination_path: str) -> Tuple[bool, str]:
        """Retrieve a backup file.
        
        Args:
            website_name: The name of the website
            backup_name: Name of the backup to retrieve
            destination_path: Path where to save the retrieved backup
        
        Returns:
            Tuple of (success, file_path or error_message)
        """
        pass
    
    @abstractmethod
    def list_backups(self, website_name: Optional[str] = None) -> List[Dict]:
        """List available backups.
        
        Args:
            website_name: Optional filter for website backups
        
        Returns:
            List of backup information dictionaries
        """
        pass
    
    @abstractmethod
    def delete_backup(self, website_name: str, backup_name: str) -> Tuple[bool, str]:
        """Delete a backup.
        
        Args:
            website_name: The name of the website
            backup_name: Name of the backup to delete
        
        Returns:
            Tuple of (success, message)
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this storage provider.
        
        Returns:
            Provider name as string
        """
        pass
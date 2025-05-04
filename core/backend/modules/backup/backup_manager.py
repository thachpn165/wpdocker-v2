#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
from typing import Dict, List, Optional, Tuple, Union, Any

from core.backend.utils.debug import Debug
from core.backend.utils.env_utils import get_env_value
from core.backend.modules.backup.storage.base import StorageProvider
from core.backend.modules.backup.storage.local_storage import LocalStorage
from core.backend.modules.backup.storage.rclone_storage import RcloneStorage
from core.backend.modules.website.website_utils import get_site_config
from core.backend.modules.backup.website_backup import backup_website as backup_website_func


class BackupManager:
    """Central manager for backup operations."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(BackupManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the backup manager."""
        if self._initialized:
            return
            
        self._initialized = True
        self.debug = Debug("BackupManager")
        
        # Initialize storage providers
        self.storage_providers = {}
        self._init_storage_providers()
        
        # Temporary directory for operations
        self.temp_dir = os.path.join(get_env_value("BACKUP_DIR"), "temp")
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def _init_storage_providers(self):
        """Initialize available storage providers."""
        # Add local storage provider by default
        self.add_storage_provider("local", LocalStorage())
        
        # Check for available Rclone remotes and add them as providers
        try:
            from core.backend.modules.rclone.rclone_manager import RcloneManager
            rclone_manager = RcloneManager()
            remotes = rclone_manager.list_remotes()
            
            for remote in remotes:
                provider_name = f"rclone:{remote}"
                self.add_storage_provider(provider_name, RcloneStorage(remote))
                self.debug.info(f"Added Rclone storage provider for remote '{remote}'")
        except Exception as e:
            self.debug.warn(f"Failed to initialize Rclone storage providers: {str(e)}")
    
    def add_storage_provider(self, provider_name: str, provider: StorageProvider):
        """Add a storage provider.
        
        Args:
            provider_name: Name of the provider
            provider: StorageProvider instance
        """
        self.storage_providers[provider_name] = provider
        self.debug.info(f"Added storage provider: {provider_name}")
    
    def get_storage_provider(self, provider_name: str) -> Optional[StorageProvider]:
        """Get a storage provider by name.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            StorageProvider instance or None if not found
        """
        return self.storage_providers.get(provider_name)
    
    def get_available_providers(self) -> List[str]:
        """Get a list of available storage provider names.
        
        Returns:
            List of provider names
        """
        return list(self.storage_providers.keys())
    
    def create_backup(self, website_name: str, storage_provider: Optional[str] = "local") -> Tuple[bool, str]:
        """Create a backup for a website and store it using the specified provider.
        
        Args:
            website_name: Name of the website to backup
            storage_provider: Name of the storage provider to use (default: local)
            
        Returns:
            Tuple of (success, backup_path or error_message)
        """
        self.debug.info(f"Creating backup for website '{website_name}' using provider '{storage_provider}'")
        
        # Check if storage provider exists
        provider = self.get_storage_provider(storage_provider)
        if not provider:
            error_message = f"Storage provider '{storage_provider}' not found"
            self.debug.error(error_message)
            return False, error_message
        
        try:
            # Create backup using existing function
            local_backup_path = backup_website_func(website_name)
            
            if not local_backup_path or not os.path.exists(local_backup_path):
                error_message = f"Failed to create backup for website '{website_name}'"
                self.debug.error(error_message)
                return False, error_message
            
            # Store backup using the selected provider
            success, result = provider.store_backup(website_name, local_backup_path)
            
            if success:
                self.debug.success(f"Backup for website '{website_name}' created and stored successfully")
                return True, result
            else:
                error_message = f"Failed to store backup: {result}"
                self.debug.error(error_message)
                return False, error_message
        except Exception as e:
            error_message = f"Error creating backup: {str(e)}"
            self.debug.error(error_message)
            return False, error_message
    
    def restore_backup(self, website_name: str, backup_name: str, 
                      storage_provider: Optional[str] = "local") -> Tuple[bool, str]:
        """Restore a backup for a website from the specified provider.
        
        Args:
            website_name: Name of the website to restore
            backup_name: Name of the backup to restore
            storage_provider: Name of the storage provider to use (default: local)
            
        Returns:
            Tuple of (success, message)
        """
        self.debug.info(f"Restoring backup '{backup_name}' for website '{website_name}' "
                      f"from provider '{storage_provider}'")
        
        # Check if storage provider exists
        provider = self.get_storage_provider(storage_provider)
        if not provider:
            error_message = f"Storage provider '{storage_provider}' not found"
            self.debug.error(error_message)
            return False, error_message
        
        try:
            # Create temporary file for the backup
            temp_file = os.path.join(self.temp_dir, backup_name)
            
            # Retrieve backup from the provider
            success, result = provider.retrieve_backup(website_name, backup_name, temp_file)
            
            if not success:
                error_message = f"Failed to retrieve backup: {result}"
                self.debug.error(error_message)
                return False, error_message
            
            # Restore the backup
            from core.backend.modules.backup.backup_restore import restore_database, restore_source_code
            
            # Determine backup type and restore accordingly
            is_database = backup_name.endswith('.sql')
            is_archive = backup_name.endswith('.tar.gz') or backup_name.endswith('.tgz')
            
            restore_success = False
            
            if is_database:
                # Restore database
                self.debug.info(f"Restoring database from {temp_file}")
                restore_success = restore_database(website_name, temp_file)
            elif is_archive:
                # Restore source code
                self.debug.info(f"Restoring source code from {temp_file}")
                restore_success = restore_source_code(website_name, temp_file)
            else:
                error_message = f"Unknown backup file type: {backup_name}"
                self.debug.error(error_message)
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return False, error_message
            
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            if restore_success:
                # Restart the website
                from core.backend.modules.backup.backup_restore import restart_website
                restart_result = restart_website(website_name)
                
                if not restart_result:
                    self.debug.warn(f"Website '{website_name}' restored but could not be restarted automatically")
                
                self.debug.success(f"Backup '{backup_name}' for website '{website_name}' restored successfully")
                return True, f"Backup '{backup_name}' restored successfully"
            else:
                error_message = f"Failed to restore backup '{backup_name}'"
                self.debug.error(error_message)
                return False, error_message
        except Exception as e:
            error_message = f"Error restoring backup: {str(e)}"
            self.debug.error(error_message)
            return False, error_message
    
    def list_backups(self, website_name: Optional[str] = None,
                    storage_provider: Optional[str] = None) -> List[Dict]:
        """List available backups.
        
        Args:
            website_name: Optional filter for website backups
            storage_provider: Optional filter for storage provider
            
        Returns:
            List of backup information dictionaries
        """
        all_backups = []
        
        try:
            # If storage_provider is specified, only list backups from that provider
            if storage_provider:
                provider = self.get_storage_provider(storage_provider)
                if provider:
                    backups = provider.list_backups(website_name)
                    all_backups.extend(backups)
            else:
                # List backups from all providers
                for provider_name, provider in self.storage_providers.items():
                    try:
                        backups = provider.list_backups(website_name)
                        all_backups.extend(backups)
                    except Exception as e:
                        self.debug.warn(f"Error listing backups from provider '{provider_name}': {str(e)}")
            
            # Sort backups by modification time (newest first)
            all_backups.sort(key=lambda x: x.get("modified", 0), reverse=True)
            
        except Exception as e:
            self.debug.error(f"Error listing backups: {str(e)}")
        
        return all_backups
    
    def delete_backup(self, website_name: str, backup_name: str,
                     storage_provider: str) -> Tuple[bool, str]:
        """Delete a backup.
        
        Args:
            website_name: Name of the website
            backup_name: Name of the backup to delete
            storage_provider: Name of the storage provider
            
        Returns:
            Tuple of (success, message)
        """
        self.debug.info(f"Deleting backup '{backup_name}' for website '{website_name}' "
                       f"from provider '{storage_provider}'")
        
        # Check if storage provider exists
        provider = self.get_storage_provider(storage_provider)
        if not provider:
            error_message = f"Storage provider '{storage_provider}' not found"
            self.debug.error(error_message)
            return False, error_message
        
        try:
            # Delete backup using the provider
            success, message = provider.delete_backup(website_name, backup_name)
            
            if success:
                self.debug.success(f"Backup '{backup_name}' deleted successfully")
            else:
                self.debug.error(f"Failed to delete backup: {message}")
            
            return success, message
        except Exception as e:
            error_message = f"Error deleting backup: {str(e)}"
            self.debug.error(error_message)
            return False, error_message
    
    def schedule_backup(self, website_name: str, schedule: Dict[str, Any],
                       storage_provider: Optional[str] = "local") -> Tuple[bool, str]:
        """Schedule a backup for a website.
        
        Args:
            website_name: Name of the website
            schedule: Schedule configuration dictionary
            storage_provider: Name of the storage provider to use
            
        Returns:
            Tuple of (success, message)
        """
        self.debug.info(f"Scheduling backup for website '{website_name}' using provider '{storage_provider}'")
        
        # Check if storage provider exists
        provider = self.get_storage_provider(storage_provider)
        if not provider:
            error_message = f"Storage provider '{storage_provider}' not found"
            self.debug.error(error_message)
            return False, error_message
        
        try:
            # Get website config
            site_config = get_site_config(website_name)
            if not site_config:
                error_message = f"Website '{website_name}' not found"
                self.debug.error(error_message)
                return False, error_message
            
            # Update backup configuration in site config
            if not site_config.backup:
                from core.backend.models.config import SiteBackup, BackupSchedule, CloudConfig
                site_config.backup = SiteBackup(
                    schedule=BackupSchedule(), 
                    cloud_config=CloudConfig()
                )
            
            # Update schedule configuration
            if schedule.get("enabled", False):
                site_config.backup.schedule.enabled = True
                site_config.backup.schedule.schedule_type = schedule.get("schedule_type", "daily")
                site_config.backup.schedule.hour = schedule.get("hour", 0)
                site_config.backup.schedule.minute = schedule.get("minute", 0)
                site_config.backup.schedule.day_of_week = schedule.get("day_of_week")
                site_config.backup.schedule.day_of_month = schedule.get("day_of_month")
                site_config.backup.schedule.retention_count = schedule.get("retention_count", 3)
                
                # Update cloud configuration
                site_config.backup.cloud_config.enabled = storage_provider != "local"
                site_config.backup.cloud_config.provider = "rclone" if storage_provider.startswith("rclone:") else storage_provider
                site_config.backup.cloud_config.remote_name = storage_provider.split(":")[1] if storage_provider.startswith("rclone:") else ""
                site_config.backup.cloud_config.remote_path = "backups"
                
                # Create or update cron job
                from core.backend.modules.cron.cron_manager import CronManager
                cron_manager = CronManager()
                
                # Remove existing job if any
                if site_config.backup.job_id:
                    cron_manager.remove_job(site_config.backup.job_id)
                
                # Create cron expression based on schedule
                cron_expr = self._create_cron_expression(schedule)
                
                # Create backup script command
                script_path = f"{get_env_value('SCRIPTS_DIR')}/backup_website.sh"
                backup_cmd = f"{script_path} {website_name} --provider {storage_provider}"
                
                # Create cron job object
                from core.backend.modules.cron.models.cron_job import CronJob
                job = CronJob(
                    job_type="backup",
                    schedule=cron_expr,
                    target_id=website_name,
                    parameters={
                        "provider": storage_provider,
                        "retention_count": schedule.get("retention_count", 3)
                    },
                    description=f"Auto backup {website_name}"
                )
                
                # Add the job to crontab
                success = cron_manager.add_job(job)
                job_id = job.id if success else None
                
                if job_id:
                    site_config.backup.job_id = job_id
                    self.debug.success(f"Scheduled backup for website '{website_name}' with cron: {cron_expr}")
                else:
                    error_message = "Failed to create cron job for backup"
                    self.debug.error(error_message)
                    return False, error_message
            else:
                # Disable backup schedule
                site_config.backup.schedule.enabled = False
                
                # Remove cron job if exists
                if site_config.backup.job_id:
                    from core.backend.modules.cron.cron_manager import CronManager
                    cron_manager = CronManager()
                    cron_manager.remove_job(site_config.backup.job_id)
                    site_config.backup.job_id = None
                
                self.debug.info(f"Disabled scheduled backup for website '{website_name}'")
            
            # Update site config
            from core.backend.modules.website.website_utils import update_site_config
            update_site_config(website_name, site_config)
            
            return True, f"Backup schedule {'' if site_config.backup.schedule.enabled else 'de'}activated for website '{website_name}'"
        except Exception as e:
            error_message = f"Error scheduling backup: {str(e)}"
            self.debug.error(error_message)
            return False, error_message
    
    def _create_cron_expression(self, schedule: Dict[str, Any]) -> str:
        """Create a cron expression from a schedule configuration.
        
        Args:
            schedule: Schedule configuration dictionary
            
        Returns:
            Cron expression string
        """
        minute = schedule.get("minute", 0)
        hour = schedule.get("hour", 0)
        schedule_type = schedule.get("schedule_type", "daily")
        
        if schedule_type == "daily":
            return f"{minute} {hour} * * *"
        elif schedule_type == "weekly":
            day_of_week = schedule.get("day_of_week", 0)  # Monday is 0
            return f"{minute} {hour} * * {day_of_week}"
        elif schedule_type == "monthly":
            day_of_month = schedule.get("day_of_month", 1)
            return f"{minute} {hour} {day_of_month} * *"
        else:
            # Default to daily
            return f"{minute} {hour} * * *"
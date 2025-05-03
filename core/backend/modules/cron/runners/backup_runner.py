"""
Runner for executing scheduled website backups.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import glob
import shutil

from core.backend.utils.debug import log_call, info, error, warn, debug, success
from core.backend.modules.cron.models.cron_job import CronJob
from core.backend.modules.cron.models.job_result import JobResult
from core.backend.modules.cron.runners.base_runner import BaseRunner
from core.backend.modules.backup.website_backup import backup_website
from core.backend.modules.website.website_utils import get_site_config, get_sites_dir


class BackupRunner(BaseRunner):
    """
    Runner for executing scheduled website backups.
    
    This runner uses the backup_website function from the backup module to create backups
    and can perform additional tasks like retention management and synchronization
    with cloud storage.
    """
    
    @log_call
    def run(self, job: CronJob) -> JobResult:
        """
        Execute scheduled website backup.
        
        Args:
            job: Backup job to execute
            
        Returns:
            Execution result
        """
        # Create result object
        result = self.create_result(job, "running")
        
        try:
            # Get domain name from target_id
            domain = job.target_id
            
            # Log
            self.log(f"Starting scheduled backup for website {domain}")
            result.add_log(f"Starting backup at {result.start_time}")
            
            # Check if website exists
            site_config = get_site_config(domain)
            if not site_config:
                raise ValueError(f"Website configuration not found for domain: {domain}")
            
            # Execute backup
            self.log(f"Creating backup for website {domain}")
            backup_website(domain)
            self.log(f"Successfully created backup for website {domain}")
            
            # Manage retention count
            retention_count = job.parameters.get("retention_count", 3)
            if retention_count > 0:
                self.log(f"Managing retention of {retention_count} most recent backups")
                self._manage_retention(domain, retention_count)
            
            # Sync to cloud if configured
            if job.parameters.get("cloud_sync", False):
                self.log("Syncing backup to cloud storage")
                cloud_config = job.parameters.get("cloud_config", {})
                self._sync_to_cloud(domain, cloud_config)
            
            # Update result
            self.log("Backup completed successfully")
            result.add_log("Backup completed successfully")
            result.complete("success")
            
            # Update job status
            self.update_job_status(job, "success")
            
        except Exception as e:
            # Handle error
            error_msg = f"Error executing backup: {e}"
            self.log(error_msg)
            result.add_log(error_msg)
            result.complete("failure", str(e))
            
            # Update job status
            self.update_job_status(job, "failure")
        
        return result
    
    def _manage_retention(self, domain: str, retention_count: int):
        """
        Manage number of backup copies to keep.
        
        Args:
            domain: Website domain name
            retention_count: Number of backup copies to keep
        """
        try:
            # Get backups directory
            sites_dir = get_sites_dir()
            backup_dir = os.path.join(sites_dir, domain, "backups")
            
            if not os.path.exists(backup_dir):
                self.log(f"Backup directory not found for website {domain}")
                return
            
            # Find all backup folders
            backup_folders = [d for d in os.listdir(backup_dir) 
                             if os.path.isdir(os.path.join(backup_dir, d)) and d.startswith("backup_")]
            
            if not backup_folders:
                self.log(f"No backups found for website {domain}")
                return
            
            # Sort backup folders by creation time (newest first)
            backup_folders = sorted(
                backup_folders,
                key=lambda x: os.path.getctime(os.path.join(backup_dir, x)),
                reverse=True
            )
            
            # If number of backups exceeds retention_count, delete older ones
            if len(backup_folders) > retention_count:
                folders_to_delete = backup_folders[retention_count:]
                self.log(f"Need to delete {len(folders_to_delete)} old backups")
                
                for folder in folders_to_delete:
                    folder_path = os.path.join(backup_dir, folder)
                    self.log(f"Deleting old backup: {folder}")
                    shutil.rmtree(folder_path)
                    
                self.log(f"Deleted {len(folders_to_delete)} old backups")
            else:
                self.log(f"Number of backups ({len(backup_folders)}) has not exceeded limit ({retention_count})")
                
        except Exception as e:
            self.log(f"Error managing backup retention: {e}")
    
    def _sync_to_cloud(self, domain: str, cloud_config: Dict[str, Any]):
        """
        Sync backups to cloud storage.
        
        Args:
            domain: Website domain name
            cloud_config: Cloud storage configuration
        """
        self.log("Cloud sync feature is under development")
        
        # Check configuration
        provider = cloud_config.get("provider", "rclone")
        remote_name = cloud_config.get("remote_name", "")
        remote_path = cloud_config.get("remote_path", "")
        
        if not remote_name or not remote_path:
            self.log("Missing cloud storage configuration information")
            return
        
        self.log(f"Provider: {provider}, Remote: {remote_name}, Path: {remote_path}")
        
        # TODO: Implement cloud sync
        # This will be developed in the future
        self.log("Sync functionality will be implemented later")
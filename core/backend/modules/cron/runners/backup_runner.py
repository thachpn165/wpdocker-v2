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
from core.backend.modules.backup.backup_manager import BackupManager
from core.backend.modules.website.website_utils import get_site_config, get_sites_dir


class BackupRunner(BaseRunner):
    """
    Runner for executing scheduled website backups.
    
    This runner uses the BackupManager to create backups with support for
    different storage providers including cloud storage.
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
            
            # Get the provider from job parameters
            provider = job.parameters.get("provider", "local")
            self.log(f"Using storage provider: {provider}")
            
            # Execute backup using BackupManager
            backup_manager = BackupManager()
            
            self.log(f"Creating backup for website {domain} using provider {provider}")
            success, backup_result = backup_manager.create_backup(domain, provider)
            
            if not success:
                self.log(f"Backup failed: {backup_result}")
                raise Exception(f"Backup operation failed: {backup_result}")
                
            self.log(f"Successfully created backup for website {domain} using provider {provider}: {backup_result}")
            
            # Manage retention count
            retention_count = job.parameters.get("retention_count", 3)
            if retention_count > 0:
                self.log(f"Retention count set to {retention_count} (managed by storage provider)")
            
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
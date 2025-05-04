"""
Backup job runner.

This module provides a runner for backup jobs,
handling both local and remote backups.
"""

from src.common.logging import info, error, debug
from src.features.cron.runners.base_runner import BaseRunner
from src.features.backup.backup_manager import BackupManager


class BackupRunner(BaseRunner):
    """Runner for backup jobs."""
    
    def run(self) -> bool:
        """
        Run a backup job.
        
        Returns:
            True if successful, False otherwise
        """
        website_name = self.job.target_id
        parameters = self.job.parameters or {}
        provider = parameters.get("provider", "local")
        
        # Log start
        self.log(f"Starting backup of website {website_name} using provider {provider}")
        info(f"Running backup job for {website_name} using provider {provider}")
        
        try:
            # Create backup manager
            manager = BackupManager()
            
            # Create backup
            success, result = manager.create_backup(website_name, provider)
            
            if success:
                self.log(f"Backup successful: {result}")
                info(f"Backup job for {website_name} completed successfully")
                return True
            else:
                self.log(f"Backup failed: {result}")
                error(f"Backup job for {website_name} failed: {result}")
                return False
                
        except Exception as e:
            error_msg = f"Error running backup job for {website_name}: {str(e)}"
            self.log(error_msg)
            error(error_msg)
            return False
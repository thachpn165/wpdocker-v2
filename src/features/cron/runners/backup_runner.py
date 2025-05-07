"""
Backup job runner.

This module provides a runner for backup jobs,
handling both local and remote backups.
"""

import os
import traceback
from typing import Optional, Dict, Any

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
        try:
            website_name = self.job.target_id
            if not website_name:
                error_msg = "Backup job failed: website_name (target_id) is empty or None"
                self.log(error_msg)
                error(error_msg)
                return False
                
            parameters = self.job.parameters or {}
            
            # Make sure provider is never None
            provider = parameters.get("provider", "local")
            if provider is None:
                # Default to local if provider is explicitly None
                provider = "local"
                debug(f"Provider was None for backup job {self.job.id}, defaulting to 'local'")
            
            # Log start with extra detail
            debug(f"🐞 Website name: {website_name}, provider: {provider}")
            self.log(f"Starting backup of website {website_name} using provider {provider}")
            info(f"Running backup job for {website_name} using provider {provider}")
            
            try:
                # Create backup manager
                manager = BackupManager()
                
                # Create backup with proper error handling
                success, result = manager.create_backup(website_name, provider)
                
                if success:
                    self.log(f"Backup successful: {result}")
                    info(f"Backup job for {website_name} completed successfully")
                    return True
                else:
                    self.log(f"Backup failed: {result}")
                    error(f"Backup job for {website_name} failed: {result}")
                    return False
                    
            except TypeError as e:
                # Handle TypeError specifically (like NoneType issues) with additional context
                debug(f"🐞 Type error in backup job: {str(e)}")
                debug(f"🐞 Website name: {website_name}, type: {type(website_name)}")
                debug(f"🐞 Provider: {provider}, type: {type(provider)}")
                debug(f"🐞 Parameters: {parameters}")
                error_msg = f"Type error in backup job for {website_name}: {str(e)}"
                self.log(error_msg)
                error(error_msg)
                debug(traceback.format_exc())
                return False
                
            except Exception as e:
                # Handle other exceptions
                debug(f"🐞 Unexpected error in backup job: {str(e)}")
                error_msg = f"Error running backup job for {website_name}: {str(e)}"
                self.log(error_msg)
                error(error_msg)
                debug(traceback.format_exc())
                return False
                
        except Exception as outer_e:
            # Catch issues with job parameter extraction
            debug(f"🐞 Critical error in backup runner: {str(outer_e)}")
            error_msg = f"Critical error in backup runner: {str(outer_e)}"
            self.log(error_msg)
            error(error_msg)
            debug(traceback.format_exc())
            return False
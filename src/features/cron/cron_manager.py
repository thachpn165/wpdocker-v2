"""
Module for managing system crontab interactions.

This module provides a CronManager class for interacting with the system crontab,
allowing jobs to be added, removed, updated, and executed.
"""

import os
import sys
from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from crontab import CronTab
from datetime import datetime

from src.common.logging import log_call, info, error, warn, debug
from src.features.cron.models.cron_job import CronJob


class CronManager:
    """
    Manages interactions with the system crontab.
    
    This class provides methods to add, remove, update, and list
    cron jobs in the system. It uses the python-crontab library
    to interact with crontab and stores additional information about jobs
    in a JSON file.
    """
    
    def __init__(self, cron_user: Optional[str] = None):
        """
        Initialize CronManager.
        
        Args:
            cron_user: Crontab username (None = current user)
        """
        self.cron_user = cron_user
        
        # Explicitly use 'user=True' for current user if cron_user is None
        if cron_user is None:
            self.crontab = CronTab(user=True)
        else:
            self.crontab = CronTab(user=cron_user)
        
        # Project directory
        project_root = self._get_project_root()
        
        # Path to jobs storage file
        self.jobs_file = os.path.join(project_root, "data", "cron_jobs.json")
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.jobs_file), exist_ok=True)
        
        # Script to run jobs
        self.runner_script = os.path.join(project_root, "scripts", "cron", "run_cron_jobs.sh")
        
        # Comment marker to identify WP Docker jobs
        self.comment_marker = "wpdocker"
    
    def _get_project_root(self) -> str:
        """
        Get project root directory.
        
        Returns:
            Absolute path to project root
        """
        # Prefer environment variable if available
        if "WP_DOCKER_HOME" in os.environ:
            return os.environ["WP_DOCKER_HOME"]
        
        # Otherwise, find root directory based on current module location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # We're now in src/features/cron, so we need to go up 3 levels
        return os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    
    def _load_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Load job information from JSON file.
        
        Returns:
            Dict mapping job_id -> job information
        """
        if not os.path.exists(self.jobs_file):
            return {}
            
        try:
            with open(self.jobs_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            warn(f"⚠️ Could not read cron_jobs.json: {e}")
            return {}
    
    def _save_jobs(self, jobs_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Save job information to JSON file.
        
        Args:
            jobs_data: Dict mapping job_id -> job information
        """
        try:
            with open(self.jobs_file, "w") as f:
                json.dump(jobs_data, f, indent=2)
        except IOError as e:
            error(f"❌ Could not write to cron_jobs.json: {e}")
    
    def _get_command(self, job_id: str) -> str:
        """
        Create command to execute cron job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Command string
        """
        return f"{self.runner_script} {job_id}"
    
    def _get_comment(self, job_id: str) -> str:
        """
        Create comment for cron job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Comment string
        """
        return f"{self.comment_marker}_{job_id}"
        
    def _set_job_enabled(self, job: Any, enabled: bool) -> None:
        """
        Safely set a job's enabled state, compatible with different python-crontab versions.
        
        Args:
            job: The crontab job object
            enabled: Whether the job should be enabled
        """
        # Handle different versions of python-crontab
        try:
            # Try property-based approach (newer versions)
            is_property = isinstance(getattr(type(job), 'enabled', None), property)
            if is_property:
                job.enabled = enabled
            else:
                # Use method-based approach (older versions)
                if enabled:
                    job.enable()
                else:
                    job.disable()
        except (AttributeError, TypeError):
            # Fallback to directly setting the property
            try:
                job.enabled = enabled
            except Exception as e:
                warn(f"⚠️ Could not set job enabled state: {e}")
                # Final fallback - use internal _enabled attribute if available
                try:
                    job._enabled = enabled
                except:
                    pass
    
    @log_call
    def add_job(self, job: CronJob) -> bool:
        """
        Add a job to crontab.
        
        Args:
            job: CronJob object describing the job
            
        Returns:
            True if successful, False if error
        """
        try:
            # Check if job already exists
            jobs_data = self._load_jobs()
            if job.id in jobs_data:
                warn(f"⚠️ Job with ID {job.id} already exists.")
                return False
            
            # Add job to crontab
            cron_job = self.crontab.new(
                command=self._get_command(job.id),
                comment=self._get_comment(job.id)
            )
            cron_job.setall(job.schedule)
            
            # Set enabled state explicitly 
            self._set_job_enabled(cron_job, job.enabled)
            
            # Save to crontab
            self.crontab.write()
            
            # Add job information to JSON file
            jobs_data[job.id] = job.to_dict()
            self._save_jobs(jobs_data)
            
            info(f"✅ Added job {job.id} to crontab.")
            return True
            
        except Exception as e:
            error(f"❌ Error adding job to crontab: {e}")
            return False
    
    @log_call
    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from crontab.
        
        Args:
            job_id: ID of job to remove
            
        Returns:
            True if successful, False if error
        """
        try:
            # Remove job from crontab
            comment = self._get_comment(job_id)
            count = 0
            for job in self.crontab.find_comment(comment):
                self.crontab.remove(job)
                count += 1
            
            if count == 0:
                warn(f"⚠️ No job with ID {job_id} found in crontab.")
            
            # Save crontab
            self.crontab.write()
            
            # Remove job information from JSON file
            jobs_data = self._load_jobs()
            if job_id in jobs_data:
                del jobs_data[job_id]
                self._save_jobs(jobs_data)
                info(f"✅ Removed job {job_id} from crontab.")
                return True
            else:
                warn(f"⚠️ No job information found with ID {job_id}.")
                return count > 0
            
        except Exception as e:
            error(f"❌ Error removing job from crontab: {e}")
            return False
    
    @log_call
    def update_job(self, job: CronJob) -> bool:
        """
        Update a job in crontab.
        
        Args:
            job: CronJob object with new information
            
        Returns:
            True if successful, False if error
        """
        try:
            # Check if job exists
            jobs_data = self._load_jobs()
            if job.id not in jobs_data:
                warn(f"⚠️ No job found with ID {job.id}.")
                return False
            
            # Remove old job
            comment = self._get_comment(job.id)
            for old_job in self.crontab.find_comment(comment):
                self.crontab.remove(old_job)
            
            # Add new job
            cron_job = self.crontab.new(
                command=self._get_command(job.id),
                comment=comment
            )
            cron_job.setall(job.schedule)
            
            # Set enabled state explicitly
            self._set_job_enabled(cron_job, job.enabled)
            
            # Save crontab
            self.crontab.write()
            
            # Update job information in JSON file
            jobs_data[job.id] = job.to_dict()
            self._save_jobs(jobs_data)
            
            info(f"✅ Updated job {job.id} in crontab.")
            return True
            
        except Exception as e:
            error(f"❌ Error updating job in crontab: {e}")
            return False
    
    @log_call
    def disable_job(self, job_id: str) -> bool:
        """
        Temporarily disable a job.
        
        Args:
            job_id: ID of job to disable
            
        Returns:
            True if successful, False if error
        """
        try:
            # Check if job exists
            jobs_data = self._load_jobs()
            if job_id not in jobs_data:
                warn(f"⚠️ No job found with ID {job_id}.")
                return False
            
            # Disable job in crontab
            comment = self._get_comment(job_id)
            count = 0
            for job in self.crontab.find_comment(comment):
                self._set_job_enabled(job, False)
                count += 1
            
            if count == 0:
                warn(f"⚠️ No job with ID {job_id} found in crontab.")
                return False
            
            # Save crontab
            self.crontab.write()
            
            # Update status in JSON file
            jobs_data[job_id]["enabled"] = False
            self._save_jobs(jobs_data)
            
            info(f"✅ Disabled job {job_id}.")
            return True
            
        except Exception as e:
            error(f"❌ Error disabling job: {e}")
            return False
    
    @log_call
    def enable_job(self, job_id: str) -> bool:
        """
        Re-enable a disabled job.
        
        Args:
            job_id: ID of job to enable
            
        Returns:
            True if successful, False if error
        """
        try:
            # Check if job exists
            jobs_data = self._load_jobs()
            if job_id not in jobs_data:
                warn(f"⚠️ No job found with ID {job_id}.")
                return False
            
            # Enable job in crontab
            comment = self._get_comment(job_id)
            count = 0
            for job in self.crontab.find_comment(comment):
                self._set_job_enabled(job, True)
                count += 1
            
            if count == 0:
                warn(f"⚠️ No job with ID {job_id} found in crontab.")
                return False
            
            # Save crontab
            self.crontab.write()
            
            # Update status in JSON file
            jobs_data[job_id]["enabled"] = True
            self._save_jobs(jobs_data)
            
            info(f"✅ Enabled job {job_id}.")
            return True
            
        except Exception as e:
            error(f"❌ Error enabling job: {e}")
            return False
    
    @log_call
    def list_jobs(self) -> List[CronJob]:
        """
        List all registered jobs.
        
        Returns:
            List of CronJob objects
        """
        try:
            jobs_data = self._load_jobs()
            return [CronJob.from_dict(data) for data in jobs_data.values()]
        except Exception as e:
            error(f"❌ Error listing jobs: {e}")
            return []
    
    @log_call
    def get_job(self, job_id: str) -> Optional[CronJob]:
        """
        Get information about a specific job.
        
        Args:
            job_id: ID of job to find
            
        Returns:
            CronJob object or None if not found
        """
        try:
            jobs_data = self._load_jobs()
            if job_id in jobs_data:
                return CronJob.from_dict(jobs_data[job_id])
            else:
                warn(f"⚠️ No job found with ID {job_id}.")
                return None
        except Exception as e:
            error(f"❌ Error getting job information: {e}")
            return None
    
    @log_call
    def update_job_status(self, job_id: str, status: str, last_run: Optional[str] = None) -> bool:
        """
        Update a job's status.
        
        Args:
            job_id: ID of job to update
            status: New status (success, failure, etc)
            last_run: Last run time (defaults to current time)
            
        Returns:
            True if successful, False if error
        """
        try:
            # Check if job exists
            jobs_data = self._load_jobs()
            if job_id not in jobs_data:
                warn(f"⚠️ No job found with ID {job_id}.")
                return False
            
            # Update status
            jobs_data[job_id]["last_status"] = status
            jobs_data[job_id]["last_run"] = last_run or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Save changes
            self._save_jobs(jobs_data)
            
            debug(f"✅ Updated status of job {job_id} to {status}.")
            return True
            
        except Exception as e:
            error(f"❌ Error updating job status: {e}")
            return False
    
    @log_call
    def run_job(self, job_id: str) -> bool:
        """
        Run a job immediately.
        
        Args:
            job_id: ID of job to run
            
        Returns:
            True if successful, False if error
        """
        try:
            job = self.get_job(job_id)
            if not job:
                return False
            
            # Update status
            self.update_job_status(job_id, "running")
            
            # Run command
            command = self._get_command(job_id)
            info(f"🔄 Running job {job_id}: {command}")
            
            # Execute command
            os.system(command)
            
            return True
            
        except Exception as e:
            error(f"❌ Error running job: {e}")
            return False
"""
Module defining the base class for cron job runners.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.backend.utils.debug import log_call, info, error, warn, debug
from core.backend.modules.cron.models.cron_job import CronJob
from core.backend.modules.cron.models.job_result import JobResult


class BaseRunner(ABC):
    """
    Base class for all cron job runners.
    
    Each job type will have a dedicated runner inheriting from this class and implementing
    the logic to execute that specific job type.
    """
    
    def __init__(self):
        """Initialize the runner."""
        self.logs = []
    
    @abstractmethod
    def run(self, job: CronJob) -> JobResult:
        """
        Execute the job and return the result.
        
        Args:
            job: Job to execute
            
        Returns:
            Job execution result
        """
        pass
    
    def log(self, message: str):
        """
        Log execution messages.
        
        Args:
            message: Message to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.logs.append(log_message)
        debug(log_message)
    
    def update_job_status(self, job: CronJob, status: str, details: Dict[str, Any] = None):
        """
        Update job status after execution.
        
        Args:
            job: Job to update
            status: New status (success, failure, etc)
            details: Additional detailed information (optional)
        """
        from core.backend.modules.cron.cron_manager import CronManager
        
        # Update status
        manager = CronManager()
        manager.update_job_status(job.id, status)
        
        # Log
        self.log(f"Updated job {job.id} status to {status}")
    
    def create_result(self, job: CronJob, status: str = "running") -> JobResult:
        """
        Create a new result object.
        
        Args:
            job: Job being executed
            status: Initial status
            
        Returns:
            New JobResult object
        """
        return JobResult(
            job_id=job.id,
            status=status,
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            logs=self.logs.copy()
        )
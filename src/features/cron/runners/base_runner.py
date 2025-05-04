"""
Base class for cron job runners.

This module provides a base class for job runners,
defining the interface that all runners must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from src.features.cron.models.cron_job import CronJob
from src.features.cron.models.job_result import JobResult


class BaseRunner(ABC):
    """Base class for all job runners."""
    
    def __init__(self, job: CronJob, job_result: JobResult):
        """
        Initialize the runner.
        
        Args:
            job: The job to run
            job_result: The job result to update
        """
        self.job = job
        self.job_result = job_result
    
    @abstractmethod
    def run(self) -> bool:
        """
        Run the job.
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def log(self, message: str) -> None:
        """
        Add a log entry to the job result.
        
        Args:
            message: Log message
        """
        self.job_result.add_log(message)
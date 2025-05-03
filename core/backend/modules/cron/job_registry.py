"""
Module for registering and managing cron job types.
"""
from typing import Dict, Any, Type, Optional
import importlib
import inspect
from datetime import datetime

from core.backend.utils.debug import log_call, info, error, warn, debug
from core.backend.modules.cron.models.cron_job import CronJob
from core.backend.modules.cron.models.job_result import JobResult
from core.backend.modules.cron.runners.base_runner import BaseRunner


class JobRegistry:
    """
    Registry for managing cron job types.
    
    This class maintains a mapping from job types to corresponding runner classes
    and provides methods to register, find, and execute different types of jobs.
    """
    
    _instance = None
    
    def __new__(cls):
        """Ensure only one instance of JobRegistry exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(JobRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the registry."""
        if self._initialized:
            return
            
        self.runner_map = {}  # Map from job_type -> runner class
        self._initialized = True
        
        # Auto-register all available runners
        self._auto_register_runners()
    
    def _auto_register_runners(self):
        """Automatically find and register all available runners."""
        try:
            # Import runners module
            from core.backend.modules.cron.runners import base_runner
            runners_module = importlib.import_module("core.backend.modules.cron.runners")
            
            # Iterate through all submodules in the runners module
            for file_name in runners_module.__all__:
                if file_name == "base_runner":
                    continue
                    
                try:
                    # Import submodule
                    module = importlib.import_module(f"core.backend.modules.cron.runners.{file_name}")
                    
                    # Find all classes in submodule
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # If class is a subclass of BaseRunner and not BaseRunner itself
                        if issubclass(obj, BaseRunner) and obj != BaseRunner:
                            # Get job type from class name
                            job_type = file_name.replace("_runner", "")
                            
                            # Register runner
                            self.register_runner(job_type, obj)
                            debug(f"✅ Auto-registered runner {name} for job type {job_type}")
                            
                except (ImportError, AttributeError) as e:
                    warn(f"⚠️ Could not register runner from {file_name}: {e}")
                    
        except ImportError as e:
            warn(f"⚠️ Could not auto-register runners: {e}")
    
    @log_call
    def register_runner(self, job_type: str, runner_class: Type[BaseRunner]):
        """
        Register a runner for a job type.
        
        Args:
            job_type: Job type
            runner_class: Corresponding runner class
        """
        if not issubclass(runner_class, BaseRunner):
            raise TypeError(f"Runner class must be a subclass of BaseRunner")
            
        self.runner_map[job_type] = runner_class
        debug(f"✅ Registered runner for job type {job_type}")
    
    @log_call
    def get_runner(self, job_type: str) -> Optional[Type[BaseRunner]]:
        """
        Get runner for a specific job type.
        
        Args:
            job_type: Job type
            
        Returns:
            Runner class or None if not found
        """
        if job_type in self.runner_map:
            return self.runner_map[job_type]
            
        warn(f"⚠️ No runner found for job type: {job_type}")
        return None
    
    @log_call
    def execute_job(self, job: CronJob) -> JobResult:
        """
        Execute a specific job.
        
        Args:
            job: Job to execute
            
        Returns:
            Execution result
        """
        runner_class = self.get_runner(job.job_type)
        
        if not runner_class:
            result = JobResult(
                job_id=job.id,
                status="failure",
                start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                error=f"No runner found for job type: {job.job_type}"
            )
            result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return result
        
        try:
            # Create runner instance
            runner = runner_class()
            
            # Execute job
            info(f"🔄 Executing job {job.id} (Type: {job.job_type})")
            result = runner.run(job)
            
            return result
            
        except Exception as e:
            error(f"❌ Error executing job {job.id}: {e}")
            
            # Create error result
            result = JobResult(
                job_id=job.id,
                status="failure",
                start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                error=str(e)
            )
            result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return result
    
    @log_call
    def get_available_job_types(self) -> Dict[str, str]:
        """
        Get list of registered job types.
        
        Returns:
            Dict mapping job_type -> runner class name
        """
        return {job_type: runner_class.__name__ for job_type, runner_class in self.runner_map.items()}
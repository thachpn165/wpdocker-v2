"""
Job runner registry for cron jobs.

This module provides a registry for job runners based on job type,
allowing appropriate runners to be selected for different job types.
"""

from typing import Dict, Type, Optional, Any


# Import runner classes
def _import_runners():
    """Import all runner classes."""
    from src.features.cron.runners.base_runner import BaseRunner
    
    try:
        from src.features.cron.runners.backup_runner import BackupRunner
        return {
            "backup": BackupRunner
        }
    except ImportError:
        # If backup runner is not available, return empty registry
        return {}


# Job type to runner class mapping
_RUNNERS: Dict[str, Type] = {}


def get_runner_for_job_type(job_type: str) -> Optional[Type]:
    """
    Get the appropriate runner class for a job type.
    
    Args:
        job_type: Type of job
        
    Returns:
        Runner class or None if not found
    """
    global _RUNNERS
    
    if not _RUNNERS:
        _RUNNERS = _import_runners()
        
    return _RUNNERS.get(job_type)


def get_available_job_types() -> list:
    """
    Get a list of available job types.
    
    Returns:
        List of job type names
    """
    global _RUNNERS
    
    if not _RUNNERS:
        _RUNNERS = _import_runners()
        
    return list(_RUNNERS.keys())
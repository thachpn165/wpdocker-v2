"""
Backup management prompts.

This package contains modules for interactive backup management,
including creation, restoration, scheduling, and cloud integration prompts.
"""

from src.features.backup.prompts.prompt_cloud_backup import prompt_restore_from_cloud

__all__ = ['prompt_restore_from_cloud']
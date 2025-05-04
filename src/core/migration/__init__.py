"""
Migration utilities for transitioning from old structure to new structure.

This module provides utilities for helping with the migration from
the old directory structure to the new refactored structure.
"""

from src.core.migration.path_mapping import (
    OLD_TO_NEW_PATHS, 
    IMPORT_PATTERNS,
    ENV_VAR_CHANGES,
    get_new_path,
    update_import_statement
)

__all__ = [
    'OLD_TO_NEW_PATHS', 
    'IMPORT_PATTERNS',
    'ENV_VAR_CHANGES',
    'get_new_path',
    'update_import_statement'
]
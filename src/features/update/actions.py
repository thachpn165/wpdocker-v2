"""
Action functions for update operations.

This module provides high-level action functions that interact with
the UpdateManager to perform update-related tasks.
"""

from typing import Dict, Any

from src.common.logging import log_call
from src.features.update.manager import UpdateManager


@log_call
def check_version_action() -> Dict[str, Any]:
    """
    Check the current version and available updates.
    
    Returns:
        Dict containing version information and update status
    """
    manager = UpdateManager()
    version, channel = manager.get_current_version()
    
    result = {
        "current_version": version,
        "channel": channel,
        "update_available": False,
        "update_info": None
    }
    
    update_info = manager.check_for_updates()
    if update_info:
        result["update_available"] = True
        result["update_info"] = update_info
        
    return result


@log_call
def update_action() -> Dict[str, Any]:
    """
    Update to the latest version.
    
    Returns:
        Dict containing success status and result message
    """
    manager = UpdateManager()
    
    # Check for updates
    update_info = manager.check_for_updates()
    if not update_info:
        return {
            "success": False,
            "message": "You are already using the latest version"
        }
        
    # Apply the update
    success = manager.update()
    
    return {
        "success": success,
        "message": "Update successful" if success else "Update failed"
    }
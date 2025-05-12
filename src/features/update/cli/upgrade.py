"""
Command-line interface for applying updates.

This module provides command-line functionality for applying
updates to the WP Docker application.
"""

from typing import Dict, Any, Optional

from src.common.logging import log_call, debug, info, success, warn, error
from src.features.update.actions import check_version_action, update_action


@log_call
def get_upgrade_params() -> Dict[str, Any]:
    """
    Get parameters for upgrade operation.
    
    For upgrade, we don't need any additional parameters.
    
    Returns:
        Empty dict as there are no parameters
    """
    return {}


@log_call
def cli_upgrade(interactive: bool = True) -> bool:
    """
    Apply available updates.
    
    Args:
        interactive: Whether this is being run interactively
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # First check if updates are available
        check_result = check_version_action()
        
        if not check_result["update_available"]:
            if interactive:
                info("You are already using the latest version")
            return True
        
        # Show what will be updated
        if interactive:
            update_info = check_result["update_info"]
            current_version = check_result["current_version"]
            new_version = update_info.get("version", "unknown")
            
            info(f"Updating from {current_version} to {new_version}...")
        
        # Apply the update
        result = update_action()
        
        if interactive:
            if result["success"]:
                success("Update completed successfully")
                info("Please restart the application to use the new version")
            else:
                error(f"Update failed: {result['message']}")
        
        return result["success"]
    except Exception as e:
        error(f"Error during update: {str(e)}")
        return False
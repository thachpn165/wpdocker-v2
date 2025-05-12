"""
Command-line interface for checking for updates.

This module provides command-line functionality for checking
if updates are available for the WP Docker application.
"""

from typing import Dict, Any, Optional, Tuple

from src.common.logging import log_call, debug, info, success, warn, error
from src.features.update.actions import check_version_action


@log_call
def get_version_check_params() -> Dict[str, Any]:
    """
    Get parameters for version check.
    
    For version check, we don't need any additional parameters.
    
    Returns:
        Empty dict as there are no parameters
    """
    return {}


@log_call
def cli_check_version(interactive: bool = True) -> bool:
    """
    Check for updates and display results.
    
    Args:
        interactive: Whether this is being run interactively
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = check_version_action()
        
        if interactive:
            # Display results to the user
            current_version = result["current_version"]
            channel = result["channel"]
            
            info(f"Current version: {current_version} ({channel})")
            
            if result["update_available"]:
                update_info = result["update_info"]
                version = update_info.get("version", "unknown")
                success(f"New version available: {version}")
                
                if "notes" in update_info and update_info["notes"]:
                    info(f"Release notes: {update_info['notes']}")
                    
                info("Run 'wpdocker update' to update to the latest version")
            else:
                info("You are using the latest version")
                
        return True
    except Exception as e:
        error(f"Error checking for updates: {str(e)}")
        return False
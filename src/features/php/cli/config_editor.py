"""
CLI interface for PHP configuration editing.

This module provides a command-line interface for editing PHP configuration files
for websites.
"""

import sys
from questionary import select, confirm
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import select_website
from src.features.php.config import (
    edit_php_ini,
    edit_php_fpm_pool,
    backup_php_config,
    restore_php_config_backup
)


@log_call
def prompt_edit_php_config() -> Optional[Dict[str, Any]]:
    """
    Prompt the user for PHP configuration editing parameters.
    
    Returns:
        Optional[Dict[str, Any]]: Dictionary with domain and config_type if successful,
                                 None if cancelled
    """
    try:
        # Select website
        domain = select_website("Select website to edit PHP configuration:")
        
        if not domain:
            warn("No website selected or no websites available.")
            return None
        
        # Select configuration type
        config_type = select(
            "Select configuration to edit:",
            choices=[
                "php.ini - Main PHP configuration",
                "php-fpm.conf - Process manager configuration"
            ]
        ).ask()
        
        if not config_type:
            return None
            
        # Ask if user wants to backup configuration
        backup = confirm(
            "Do you want to backup the configuration files before editing?"
        ).ask()
        
        return {
            "domain": domain,
            "config_type": config_type.split(" - ")[0],  # Extract file name
            "backup": backup
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_edit_php_config() -> bool:
    """
    CLI entry point for editing PHP configuration.
    
    Returns:
        bool: True if edit was successful, False otherwise
    """
    params = prompt_edit_php_config()
    if not params:
        return False
    
    domain = params["domain"]
    config_type = params["config_type"]
    backup = params["backup"]
    
    # Backup configuration if requested
    if backup:
        backup_dir = backup_php_config(domain)
        if not backup_dir:
            warn("Could not create configuration backup. Continuing with edit...")
        else:
            success(f"Configuration backed up to: {backup_dir}")
    
    # Edit configuration
    if config_type == "php.ini":
        edit_result = edit_php_ini(domain)
    elif config_type == "php-fpm.conf":
        edit_result = edit_php_fpm_pool(domain)
    else:
        error(f"Unknown configuration type: {config_type}")
        return False
    
    if not edit_result:
        error("Error editing PHP configuration.")
        return False
    
    success("PHP configuration edited successfully.")
    
    # If we made a backup, ask if the user wants to restore it
    if backup and backup_dir:
        restore = confirm(
            "Do you want to restore the configuration backup? "
            "(Only necessary if you made mistakes during editing)"
        ).ask()
        
        if restore:
            restore_result = restore_php_config_backup(domain)
            if restore_result:
                success("PHP configuration backup has been restored successfully.")
            else:
                error("Error restoring PHP configuration backup.")
    
    return True


if __name__ == "__main__":
    success = cli_edit_php_config()
    sys.exit(0 if success else 1)
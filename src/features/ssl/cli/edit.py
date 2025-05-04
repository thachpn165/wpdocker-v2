"""
CLI interface for editing SSL certificates.

This module provides a command-line interface for editing SSL certificates
installed on websites.
"""

import sys
from questionary import confirm, select
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import select_website
from src.features.ssl.editor import edit_ssl, backup_ssl_files, restore_ssl_backup


@log_call
def cli_edit_ssl() -> bool:
    """
    CLI entry point for editing SSL certificates.
    
    Returns:
        bool: True if editing was successful, False otherwise
    """
    domain = select_website("Select website to edit SSL certificate:")
    
    if not domain:
        warn("No website selected or no websites available.")
        return False
    
    # Ask if the user wants to backup the SSL files first
    backup = confirm(
        "Do you want to backup the SSL files before editing?"
    ).ask()
    
    if backup:
        backup_dir = backup_ssl_files(domain)
        if not backup_dir:
            warn("Could not create SSL backup. Continuing with edit...")
        else:
            success(f"SSL files backed up to: {backup_dir}")
    
    # Edit the SSL files
    edit_result = edit_ssl(domain)
    
    if not edit_result:
        error("Error editing SSL files.")
        return False
    
    success("SSL files have been edited successfully.")
    
    # If we made a backup, ask if the user wants to restore it
    if backup and backup_dir:
        restore = confirm(
            "Do you want to restore the SSL backup? "
            "(Only necessary if you made mistakes during editing)"
        ).ask()
        
        if restore:
            restore_result = restore_ssl_backup(domain)
            if restore_result:
                success("SSL backup has been restored successfully.")
            else:
                error("Error restoring SSL backup.")
    
    return True


if __name__ == "__main__":
    success = cli_edit_ssl()
    sys.exit(0 if success else 1)
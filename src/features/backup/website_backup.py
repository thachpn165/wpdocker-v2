"""
Website backup functionality.

This module provides the main entry point for backing up a website,
coordinating the backup process for database and files.
"""

import os
from src.common.logging import log_call, info, error


@log_call
def backup_website(domain: str) -> str:
    """
    Backup an entire website (code + database) with rollback capability in case of failure.
    
    Args:
        domain: The website domain to backup
        
    Returns:
        Path to the backup file or empty string if backup failed
    """
    from src.features.website.utils import get_site_config
    from src.features.backup.backup_actions import (
        backup_create_structure,
        backup_database,
        backup_files,
        backup_update_config,
        backup_finalize,
        rollback_backup
    )
    
    info(f"🚀 Starting backup for website: {domain}")
    site_config = get_site_config(domain)
    if not site_config:
        error(f"❌ Website configuration not found for domain: {domain}")
        return ""

    try:
        # 1. Create backup directory structure
        backup_create_structure(domain)

        # 2. Backup database
        backup_database(domain)

        # 3. Backup source code (wp-content)
        backup_files(domain)
        
        # 4. Update configuration with backup information
        backup_update_config(domain)

        # 5. Finalize and add metadata
        backup_path = backup_finalize(domain)

        # Ensure we return a valid path or empty string
        if not backup_path or not isinstance(backup_path, str) or not os.path.exists(backup_path):
            error(f"❌ Final backup path invalid or file does not exist: {backup_path}")
            rollback_backup(domain)
            return ""

        info(f"✅ Website backup completed for {domain}.")
        return backup_path

    except Exception as e:
        error(f"❌ Backup failed: {e}")
        info("🔁 Rolling back...")

        # Rollback the backup process
        rollback_backup(domain)

        error(f"❌ Backup process rolled back for {domain}.")
        return ""
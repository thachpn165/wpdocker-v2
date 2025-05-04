"""
Backup action implementations.

This module provides the core functionality for backup operations,
including structure creation, database backup, file backup, and finalization.
"""

import os
import shutil
import glob
import tarfile
from datetime import datetime
from typing import Dict, Optional, Any

from src.common.logging import log_call, debug, info, warn, error
from src.common.utils.environment import env_required, get_env_value
from src.features.website.utils import get_site_config, set_site_config, get_sites_dir

# Global state for tracking backup progress
BACKUP_TEMP_STATE: Dict[str, str] = {}


@log_call
def backup_create_structure(domain: str) -> None:
    """
    Create the directory structure for a backup.
    
    Args:
        domain: The website domain to backup
    """
    sites_dir = get_sites_dir()
    debug(f"Sites dir: {sites_dir}")
    base_dir = os.path.join(sites_dir, domain, "backups")
    os.makedirs(base_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(base_dir, f"backup_{timestamp}")
    os.makedirs(backup_path)

    BACKUP_TEMP_STATE["backup_path"] = backup_path
    info(f"📁 Backup directory created: {backup_path}")


@log_call
def backup_database(domain: str) -> None:
    """
    Backup the database for a website.
    
    Args:
        domain: The website domain to backup
        
    Raises:
        RuntimeError: If backup_path is not initialized
    """
    if "backup_path" not in BACKUP_TEMP_STATE:
        raise RuntimeError("❌ backup_path not initialized.")

    target = BACKUP_TEMP_STATE["backup_path"]
    
    # Import here to avoid circular imports
    from src.features.mysql.import_export import export_database
    export_database(domain, target)
    info("💾 Database backed up successfully.")


@log_call
def backup_files(domain: str) -> None:
    """
    Backup the website files.
    
    Args:
        domain: The website domain to backup
        
    Raises:
        RuntimeError: If backup_path is not initialized
    """
    if "backup_path" not in BACKUP_TEMP_STATE:
        raise RuntimeError("❌ backup_path not initialized.")

    sites_dir = get_sites_dir()
    site_dir = os.path.join(sites_dir, domain, "wordpress")
    
    # Create a tar.gz archive instead of copying files
    backup_path = BACKUP_TEMP_STATE["backup_path"]
    archive_filename = os.path.join(backup_path, "wordpress.tar.gz")
    
    # Create the archive
    with tarfile.open(archive_filename, "w:gz") as tar:
        # Add the wordpress directory to the archive
        tar.add(site_dir, arcname="wordpress")
    
    # Store the archive path in the state
    BACKUP_TEMP_STATE["wordpress_archive"] = archive_filename
    
    info(f"📦 Website source code archive created: {archive_filename}")
    debug(f"Archive size: {os.path.getsize(archive_filename) / (1024*1024):.2f} MB")


@log_call
def backup_update_config(domain: str) -> bool:
    """
    Update the site configuration with backup information.
    
    Args:
        domain: The website domain to backup
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        RuntimeError: If backup_path is not initialized
    """
    if "backup_path" not in BACKUP_TEMP_STATE:
        raise RuntimeError("❌ backup_path not initialized.")
    
    backup_path = BACKUP_TEMP_STATE.get("backup_path")
    wordpress_archive = BACKUP_TEMP_STATE.get("wordpress_archive", "")
    
    # Find the most recent SQL file in the backup directory
    sql_files = glob.glob(os.path.join(backup_path, "*.sql"))
    database_file = ""
    if sql_files:
        # Sort by modification time, newest first
        database_file = sorted(sql_files, key=os.path.getmtime, reverse=True)[0]
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get the site configuration
    site_config = get_site_config(domain)
    if not site_config:
        error(f"❌ Configuration not found for website: {domain}")
        return False
    
    # Import necessary classes
    from src.features.website.models.site_config import SiteBackup, SiteBackupInfo
    
    # Create or update backup information
    if not hasattr(site_config, 'backup') or not site_config.backup:
        site_config.backup = SiteBackup()
    
    # Create backup info
    backup_info = SiteBackupInfo(
        time=timestamp,
        file=wordpress_archive,
        database=database_file
    )
    
    # Update the last_backup field
    site_config.backup.last_backup = backup_info
    
    # Save the updated configuration
    set_site_config(domain, site_config)
    
    info(f"📝 Backup information updated for {domain}")
    debug(f"  ⏱️  Time: {timestamp}")
    debug(f"  💾 Database: {database_file}")
    debug(f"  📦 Source code: {wordpress_archive}")
    
    return True


@log_call
def backup_finalize(domain: Optional[str] = None) -> str:
    """
    Finalize the backup process.
    
    Args:
        domain: The website domain (optional)
        
    Returns:
        Path to the backup archive
    """
    backup_path = BACKUP_TEMP_STATE.get("backup_path", "")
    wordpress_archive = BACKUP_TEMP_STATE.get("wordpress_archive", "")
    
    if backup_path:
        info(f"✅ Backup completed.")
        info(f"   📁 Backup directory: {backup_path}")
        if wordpress_archive and os.path.exists(wordpress_archive):
            archive_size = os.path.getsize(wordpress_archive) / (1024*1024)
            info(f"   📦 Website source code: {wordpress_archive} ({archive_size:.2f} MB)")
    else:
        warn("⚠️ Backup path not found to finalize the process.")
    
    # Get result path before clearing the state
    result_path = wordpress_archive
    
    # Clear the state
    BACKUP_TEMP_STATE.clear()
    
    return result_path


@log_call
def rollback_backup(domain: Optional[str] = None) -> None:
    """
    Roll back all backup operations by removing the backup directory and cleaning up config.json.
    
    Args:
        domain: The domain name of the website being backed up
    """
    # 1. Remove the backup directory
    backup_path = BACKUP_TEMP_STATE.get("backup_path")
    if backup_path and os.path.exists(backup_path):
        shutil.rmtree(backup_path)
        info(f"🗑️ Incomplete backup directory removed: {backup_path}")
    else:
        warn("⚠️ No backup directory to remove.")
    
    # 2. Clean up backup configuration in config.json
    if domain:
        try:
            # Try to get the site configuration
            site_config = get_site_config(domain)
            if site_config and hasattr(site_config, 'backup') and site_config.backup:
                # Clear backup configuration by setting it to None
                site_config.backup = None
                set_site_config(domain, site_config)
                info(f"🧹 Backup information cleared from configuration for {domain}")
        except Exception as e:
            warn(f"⚠️ Could not remove backup information from configuration: {e}")
    
    # 3. Clear the state
    BACKUP_TEMP_STATE.clear()
    info("↩️ Backup process rolled back.")
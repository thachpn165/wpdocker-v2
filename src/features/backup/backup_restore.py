"""
Backup restoration functionality.

This module provides functions for restoring website backups,
including database and file system restoration.
"""

import os
import glob
import tarfile
import shutil
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from src.common.logging import log_call, debug, info, warn, error, success
from src.features.website.utils import get_sites_dir, get_site_config


@log_call
def get_backup_folders(domain: str) -> Tuple[str, List[str], Optional[Dict[str, Any]]]:
    """
    Get all backup folders for a domain.
    
    Args:
        domain: The domain name
        
    Returns:
        Tuple of (backup_dir, backup_folders, last_backup_info)
    """
    sites_dir = get_sites_dir()
    backup_dir = os.path.join(sites_dir, domain, "backups")
    
    if not os.path.exists(backup_dir):
        error(f"❌ Backup directory not found for website {domain}.")
        return backup_dir, [], None
    
    # Find all backup folders in the backups directory
    backup_folders = [d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d)) and d.startswith("backup_")]
    
    if not backup_folders:
        error(f"❌ No backups found for website {domain}.")
        return backup_dir, [], None
    
    # Get current backup info if available
    site_config = get_site_config(domain)
    last_backup_info = None
    if site_config and hasattr(site_config, 'backup') and site_config.backup and hasattr(site_config.backup, 'last_backup'):
        last_backup_info = site_config.backup.last_backup
        
    # Sort backup folders by creation time (newest first)
    backup_folders = sorted(
        backup_folders,
        key=lambda x: os.path.getctime(os.path.join(backup_dir, x)),
        reverse=True
    )
    
    return backup_dir, backup_folders, last_backup_info


@log_call
def get_backup_info(backup_dir: str, folder: str, last_backup_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get detailed information about a backup folder.
    
    Args:
        backup_dir: The backup directory
        folder: The backup folder name
        last_backup_info: The last backup info from config (optional)
        
    Returns:
        Dictionary with backup information
    """
    folder_path = os.path.join(backup_dir, folder)
    try:
        # Get creation time
        folder_time = datetime.fromtimestamp(os.path.getctime(folder_path))
        time_str = folder_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate total size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
        
        size_str = f"{total_size / (1024*1024):.2f} MB"
        
        # Check if this is the latest backup in the configuration
        is_latest = False
        if last_backup_info and 'file' in last_backup_info:
            if last_backup_info['file'].startswith(folder_path):
                is_latest = True
        
        # Find files in the backup directory
        archive_file = None
        sql_file = None
        
        for file_path in glob.glob(os.path.join(folder_path, "*.tar.gz")):
            archive_file = file_path
            break
        
        for file_path in glob.glob(os.path.join(folder_path, "*.sql")):
            sql_file = file_path
            break
            
        return {
            "folder": folder,
            "path": folder_path,
            "time": time_str,
            "timestamp": folder_time.timestamp(),
            "size": size_str,
            "size_bytes": total_size,
            "is_latest": is_latest,
            "archive_file": archive_file,
            "sql_file": sql_file
        }
    except Exception as e:
        warn(f"⚠️ Could not get information for backup {folder}: {e}")
        return {
            "folder": folder,
            "path": folder_path,
            "error": str(e)
        }


@log_call
def restore_database(domain: str, sql_file: str, reset_db: bool = True) -> bool:
    """
    Restore database from SQL file.
    
    Args:
        domain: The domain name
        sql_file: Path to the SQL file
        reset_db: Whether to reset the database before restoring
        
    Returns:
        Success status
    """
    try:
        # Import here to avoid circular imports
        from src.features.mysql.import_export import import_database
        import_database(domain, sql_file, reset=reset_db)
        success(f"✅ Database restored successfully.")
        return True
    except Exception as e:
        error(f"❌ Error restoring database: {e}")
        return False


@log_call
def restore_source_code(domain: str, archive_file: str) -> bool:
    """
    Restore source code from archive file.
    
    Args:
        domain: The domain name
        archive_file: Path to the archive file
        
    Returns:
        Success status
    """
    sites_dir = get_sites_dir()
    wordpress_dir = os.path.join(sites_dir, domain, "wordpress")
    
    if not os.path.exists(wordpress_dir):
        error(f"❌ WordPress directory not found for website {domain}.")
        return False
        
    try:
        # Create a temporary directory for extraction
        temp_dir = os.path.join(sites_dir, domain, "temp_extract")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # Extract the tar.gz file
        with tarfile.open(archive_file, "r:gz") as tar:
            tar.extractall(path=temp_dir)
        
        # Move files from extraction directory to WordPress directory
        extracted_wordpress_dir = os.path.join(temp_dir, "wordpress")
        
        # Remove current WordPress directory
        shutil.rmtree(wordpress_dir)
        
        # Move extracted directory to new location
        shutil.move(extracted_wordpress_dir, wordpress_dir)
        
        # Set permissions
        set_wordpress_permissions(domain)
        
        # Remove temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
        success(f"✅ Source code restored successfully.")
        return True
        
    except Exception as e:
        error(f"❌ Error restoring source code: {e}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return False


@log_call
def set_wordpress_permissions(domain: str) -> bool:
    """
    Set proper permissions for WordPress files.
    
    Args:
        domain: The domain name
        
    Returns:
        Success status
    """
    try:
        # Import here to avoid circular imports
        from src.common.containers.container import Container
        
        php_container_name = f"{domain}-php"
        php_container = Container(name=php_container_name)
        
        if not php_container.running():
            warn(f"⚠️ PHP container ({php_container_name}) is not running. You may need to restart the website after restoration.")
            return False
            
        php_container.exec(["chown", "-R", "www-data:www-data", "/var/www/html"], user="root")
        info("✅ File permissions set successfully.")
        return True
    except Exception as e:
        warn(f"⚠️ Could not set permissions: {e}")
        return False


@log_call
def restart_website(domain: str) -> bool:
    """
    Restart website containers.
    
    Args:
        domain: The domain name
        
    Returns:
        Success status
    """
    try:
        sites_dir = get_sites_dir()
        compose_dir = os.path.join(sites_dir, domain, "docker-compose")
        
        if os.path.exists(compose_dir):
            cmd = ["docker-compose", "-f", os.path.join(compose_dir, "docker-compose.yml"), "restart"]
            subprocess.run(cmd, check=True)
            success(f"✅ Website {domain} restarted successfully.")
            return True
        else:
            warn(f"⚠️ Docker compose directory not found for website {domain}.")
            return False
    except Exception as e:
        error(f"❌ Error restarting website: {e}")
        return False
"""
SSL utility functions.

This module provides utility functions for SSL certificate management.
"""

import os
import shutil
from typing import Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

from src.common.logging import log_call, debug, error, info, warn
from src.common.utils.environment import env


@log_call
def get_ssl_paths(domain: str) -> Dict[str, str]:
    """
    Get SSL certificate paths for a domain.
    
    Args:
        domain: Domain name
        
    Returns:
        Dict[str, str]: Dictionary containing SSL file paths
    """
    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    return {
        "cert": os.path.join(ssl_dir, "cert.pem"),
        "key": os.path.join(ssl_dir, "key.pem"),
        "chain": os.path.join(ssl_dir, "chain.pem"),
        "fullchain": os.path.join(ssl_dir, "fullchain.pem")
    }


@log_call
def ensure_ssl_dir(domain: str) -> bool:
    """
    Ensure SSL directory exists for a domain.
    
    Args:
        domain: Domain name
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
        if not os.path.exists(ssl_dir):
            os.makedirs(ssl_dir, mode=0o755)
            info(f"Created SSL directory for {domain}")
        return True
    except Exception as e:
        error(f"Error creating SSL directory: {e}")
        return False


@log_call
def has_ssl_certificate(domain: str) -> bool:
    """
    Check if a domain has SSL certificate installed.
    
    Args:
        domain: Domain name
        
    Returns:
        bool: True if SSL certificate is installed
    """
    paths = get_ssl_paths(domain)
    return all(os.path.exists(path) for path in [paths["cert"], paths["key"]])


@log_call
def backup_ssl_files(domain: str) -> Optional[str]:
    """
    Create backup of SSL files.
    
    Args:
        domain: Domain name
        
    Returns:
        Optional[str]: Backup directory path if successful, None otherwise
    """
    try:
        ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
        if not os.path.exists(ssl_dir):
            return None
            
        backup_dir = os.path.join(ssl_dir, "backup")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, timestamp)
        os.makedirs(backup_path)
        
        for file in ["cert.pem", "key.pem", "chain.pem", "fullchain.pem"]:
            src = os.path.join(ssl_dir, file)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(backup_path, file))
                
        info(f"Created SSL backup at {backup_path}")
        return backup_path
    except Exception as e:
        error(f"Error creating SSL backup: {e}")
        return None


@log_call
def restore_ssl_backup(domain: str, backup_path: str) -> bool:
    """
    Restore SSL files from backup.
    
    Args:
        domain: Domain name
        backup_path: Path to backup directory
        
    Returns:
        bool: True if restore was successful
    """
    try:
        ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
        if not os.path.exists(backup_path):
            error(f"Backup directory not found: {backup_path}")
            return False
            
        for file in ["cert.pem", "key.pem", "chain.pem", "fullchain.pem"]:
            src = os.path.join(backup_path, file)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(ssl_dir, file))
                
        info(f"Restored SSL files from {backup_path}")
        return True
    except Exception as e:
        error(f"Error restoring SSL backup: {e}")
        return False 
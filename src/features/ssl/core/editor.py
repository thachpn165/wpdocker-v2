"""
SSL certificate editing functionality.

This module provides functions for editing SSL certificate configurations.
"""

import os
import shutil
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from src.common.logging import log_call, debug, error, info, warn
from src.features.website.utils import get_site_config, set_site_config
from src.features.ssl.utils.ssl_utils import (
    get_ssl_paths,
    backup_ssl_files,
    restore_ssl_backup
)
from src.features.ssl.models.ssl_config import SSLConfig


@log_call
def edit_ssl(
    domain: str,
    cert_path: Optional[str] = None,
    key_path: Optional[str] = None,
    chain_path: Optional[str] = None,
    auto_renew: Optional[bool] = None,
    email: Optional[str] = None
) -> bool:
    """
    Edit SSL certificate configuration.
    
    Args:
        domain: Domain name
        cert_path: Path to new certificate file
        key_path: Path to new private key file
        chain_path: Path to new certificate chain file
        auto_renew: Whether to enable auto-renewal
        email: Email address for notifications
        
    Returns:
        bool: True if edit was successful
    """
    try:
        # Get site config
        site_config = get_site_config(domain)
        if not site_config or not hasattr(site_config, "ssl"):
            error(f"SSL configuration not found for {domain}")
            return False
            
        # Create backup
        backup_path = backup_ssl_files(domain)
        if not backup_path:
            error("Failed to create backup")
            return False
            
        # Update certificate files
        paths = get_ssl_paths(domain)
        if cert_path:
            shutil.copy2(cert_path, paths["cert"])
        if key_path:
            shutil.copy2(key_path, paths["key"])
        if chain_path:
            shutil.copy2(chain_path, paths["chain"])
            
        # Update configuration
        ssl_config = site_config.ssl
        if auto_renew is not None:
            ssl_config.auto_renew = auto_renew
        if email:
            ssl_config.email = email
            
        # Update site config
        site_config.ssl = ssl_config
        set_site_config(domain, site_config)
        
        info(f"✅ Successfully updated SSL configuration for {domain}")
        return True
        
    except Exception as e:
        error(f"Error editing SSL configuration: {e}")
        if backup_path:
            restore_ssl_backup(domain, backup_path)
        return False


@log_call
def read_ssl_files(domain: str) -> Dict[str, str]:
    """
    Read SSL certificate files.
    
    Args:
        domain: Domain name
        
    Returns:
        Dict[str, str]: Dictionary containing certificate file contents
    """
    try:
        paths = get_ssl_paths(domain)
        result = {}
        
        for key, path in paths.items():
            if os.path.exists(path):
                with open(path, "r") as f:
                    result[key] = f.read()
                    
        return result
        
    except Exception as e:
        error(f"Error reading SSL files: {e}")
        return {} 
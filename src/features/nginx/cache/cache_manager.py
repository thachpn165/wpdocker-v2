"""
NGINX cache manager.

This module provides functionality for installing and managing different
types of NGINX cache configurations.
"""

import os
import shutil
from typing import List, Dict, Any, Optional, Tuple

from src.common.logging import log_call, info, debug, error, success
from src.features.nginx.utils.config_utils import (
    get_config_path,
    read_config_file,
    write_config_file,
    get_available_cache_configs
)
from src.features.nginx.manager import reload
from src.common.utils.environment import env


@log_call
def get_available_cache_types() -> List[str]:
    """
    Get a list of available cache types.
    
    Returns:
        List[str]: List of available cache types
    """
    cache_types = get_available_cache_configs()
    
    # Ensure 'no-cache' is available and first in the list for clarity
    if 'no-cache' in cache_types:
        cache_types.remove('no-cache')
    
    cache_types.insert(0, 'no-cache')
    return cache_types


@log_call
def install_cache(website: str, cache_type: str) -> Tuple[bool, str]:
    """
    Install a specific cache configuration for a website.
    
    Args:
        website: Website domain
        cache_type: Type of cache to install
    
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        # Validate inputs
        if not website:
            return False, "Website domain is required"
        
        available_caches = get_available_cache_types()
        if cache_type not in available_caches:
            valid_types = ", ".join(available_caches)
            return False, f"Invalid cache type. Available types: {valid_types}"
        
        # Get site config directory and vhost file
        sites_dir = env.get("SITES_DIR")
        if not sites_dir:
            return False, "SITES_DIR environment variable not set"
            
        site_dir = os.path.join(sites_dir, website)
        if not os.path.exists(site_dir):
            return False, f"Website directory not found: {site_dir}"
            
        nginx_conf_dir = os.path.join(site_dir, "nginx")
        os.makedirs(nginx_conf_dir, exist_ok=True)
        
        # Read cache config template
        cache_config = read_config_file("cache", cache_type)
        if not cache_config:
            return False, f"Failed to read cache configuration for type: {cache_type}"
        
        # Write cache config to site-specific include
        cache_include_path = os.path.join(nginx_conf_dir, "cache-include.conf")
        success_write = write_file_content(cache_include_path, cache_config)
        if not success_write:
            return False, f"Failed to write cache configuration to: {cache_include_path}"
        
        # Reload NGINX to apply changes
        info(f"🔄 Applying {cache_type} cache configuration for {website}...")
        reload_success = reload()
        
        if reload_success:
            success(f"✅ Successfully applied {cache_type} cache for {website}")
            
            # Return additional instructions for plugin-based caches
            if cache_type == "wp-super-cache":
                return True, "WP Super Cache configuration applied. Please install and configure the WP Super Cache plugin in WordPress."
            elif cache_type == "w3-total-cache":
                return True, "W3 Total Cache configuration applied. Please install and configure the W3 Total Cache plugin in WordPress."
            elif cache_type == "wp-fastest-cache":
                return True, "WP Fastest Cache configuration applied. Please install and configure the WP Fastest Cache plugin in WordPress."
            elif cache_type == "no-cache":
                return True, f"Cache disabled for {website}"
            else:
                return True, f"{cache_type} cache configured successfully for {website}"
        else:
            error("⚠️ Cache configuration updated but NGINX reload failed")
            return False, "Cache configuration updated but NGINX reload failed"
    except Exception as e:
        error(f"❌ Error installing cache: {str(e)}")
        return False, f"Failed to install cache: {str(e)}"


def write_file_content(file_path: str, content: str) -> bool:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file
        content: Content to write
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        error(f"Error writing to {file_path}: {str(e)}")
        return False
"""
PHP extension management functionality.

This module provides functions for managing PHP extensions,
including installation, uninstallation, and compatibility checks.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.common.logging import log_call, debug, error, info, warn
from src.common.utils.environment import env
from src.features.website.utils import get_site_config, set_site_config
from src.features.php.client import init_php_client
from src.features.php.extensions.registry import (
    EXTENSION_REGISTRY,
    get_extension_instance,
    get_extension_list
)


@log_call
def install_php_extension(domain: str, ext_id: str) -> bool:
    """
    Install a PHP extension for a website.
    
    Args:
        domain: Website domain name
        ext_id: Extension identifier
        
    Returns:
        bool: True if installation was successful, False otherwise
    """
    try:
        # Get site config
        site_config = get_site_config(domain)
        if not site_config or not hasattr(site_config, 'php') or not site_config.php:
            error(f"❌ PHP configuration not found for website {domain}")
            return False
            
        # Check if extension is already installed
        if ext_id in (site_config.php.php_installed_extensions or []):
            warn(f"⚠️ Extension '{ext_id}' is already installed")
            return True
            
        # Check if extension is registered
        if ext_id not in EXTENSION_REGISTRY:
            error(f"❌ Extension '{ext_id}' is not registered")
            return False
            
        # Get extension instance
        ext = get_extension_instance(ext_id)
        
        # Install extension
        if not ext.install(domain):
            error(f"❌ Failed to install extension '{ext_id}'")
            return False
            
        # Update configuration
        if not ext.update_config(domain):
            error(f"❌ Failed to update configuration for extension '{ext_id}'")
            return False
            
        # Update site config
        if not site_config.php.php_installed_extensions:
            site_config.php.php_installed_extensions = []
        site_config.php.php_installed_extensions.append(ext_id)
        set_site_config(domain, site_config)
        
        # Restart PHP container
        container = init_php_client(domain)
        container.restart()
        
        info(f"✅ Successfully installed extension '{ext_id}' for {domain}")
        return True
        
    except Exception as e:
        error(f"❌ Error installing PHP extension: {e}")
        return False


@log_call
def uninstall_php_extension(domain: str, ext_id: str) -> bool:
    """
    Uninstall a PHP extension from a website.
    
    Args:
        domain: Website domain name
        ext_id: Extension identifier
        
    Returns:
        bool: True if uninstallation was successful, False otherwise
    """
    try:
        # Get site config
        site_config = get_site_config(domain)
        if not site_config or not hasattr(site_config, 'php') or not site_config.php:
            error(f"❌ PHP configuration not found for website {domain}")
            return False
            
        # Check if extension is installed
        if not site_config.php.php_installed_extensions or ext_id not in site_config.php.php_installed_extensions:
            warn(f"⚠️ Extension '{ext_id}' is not installed")
            return True
            
        # Get extension instance
        ext = get_extension_instance(ext_id)
        
        # Uninstall extension
        if not ext.uninstall(domain):
            error(f"❌ Failed to uninstall extension '{ext_id}'")
            return False
            
        # Update site config
        site_config.php.php_installed_extensions.remove(ext_id)
        set_site_config(domain, site_config)
        
        # Restart PHP container
        container = init_php_client(domain)
        container.restart()
        
        info(f"✅ Successfully uninstalled extension '{ext_id}' from {domain}")
        return True
        
    except Exception as e:
        error(f"❌ Error uninstalling PHP extension: {e}")
        return False


@log_call
def get_installed_extensions(domain: str) -> List[Dict[str, Any]]:
    """
    Get a list of installed PHP extensions for a website.
    
    Args:
        domain: Website domain name
        
    Returns:
        List[Dict[str, Any]]: List of installed extensions with metadata
    """
    try:
        # Get site config
        site_config = get_site_config(domain)
        if not site_config or not hasattr(site_config, 'php') or not site_config.php:
            error(f"❌ PHP configuration not found for website {domain}")
            return []
            
        # Get installed extensions
        installed_ids = site_config.php.php_installed_extensions or []
        result = []
        
        for ext_id in installed_ids:
            try:
                if ext_id not in EXTENSION_REGISTRY:
                    warn(f"⚠️ Extension '{ext_id}' is not in the supported extensions list")
                    continue
                    
                ext = get_extension_instance(ext_id)
                result.append({
                    "id": ext.id,
                    "name": ext.name,
                    "description": ext.description,
                    "version": ext.version,
                    "requires_compilation": ext.requires_compilation
                })
            except Exception as e:
                warn(f"⚠️ Error getting information for extension '{ext_id}': {e}")
                
        return result
        
    except Exception as e:
        error(f"❌ Error getting installed extensions: {e}")
        return []


@log_call
def get_available_extensions(domain: str) -> List[Dict[str, Any]]:
    """
    Get a list of available PHP extensions for a website.
    
    Args:
        domain: Website domain name
        
    Returns:
        List[Dict[str, Any]]: List of available extensions with metadata
    """
    try:
        # Get site config
        site_config = get_site_config(domain)
        if not site_config or not hasattr(site_config, 'php') or not site_config.php:
            error(f"❌ PHP configuration not found for website {domain}")
            return []
            
        # Get installed extensions
        installed_ids = site_config.php.php_installed_extensions or []
        
        # Get all available extensions
        all_extensions = get_extension_list()
        result = []
        
        for ext_id, ext_class in all_extensions.items():
            try:
                # Skip if already installed
                if ext_id in installed_ids:
                    continue
                    
                # Create extension instance
                ext = ext_class()
                    
                result.append({
                    "id": ext.id,
                    "name": ext.name,
                    "description": ext.description,
                    "requires_compilation": ext.requires_compilation
                })
            except Exception as e:
                warn(f"⚠️ Error getting information for extension '{ext_id}': {e}")
                
        return result
        
    except Exception as e:
        error(f"❌ Error getting available extensions: {e}")
        return []


@log_call
def check_extension_status(domain: str, ext_id: str) -> Dict[str, Any]:
    """
    Check the status of a PHP extension for a website.
    
    Args:
        domain: Website domain name
        ext_id: Extension identifier
        
    Returns:
        Dict[str, Any]: Extension status information
    """
    try:
        # Get site config
        site_config = get_site_config(domain)
        if not site_config or not hasattr(site_config, 'php') or not site_config.php:
            error(f"❌ PHP configuration not found for website {domain}")
            return {"status": "error", "message": "PHP configuration not found"}
            
        # Check if extension is registered
        if ext_id not in EXTENSION_REGISTRY:
            return {
                "status": "error",
                "message": f"Extension '{ext_id}' is not registered"
            }
            
        # Get extension instance
        ext = get_extension_instance(ext_id)
        
        # Check if installed
        is_installed = ext_id in (site_config.php.php_installed_extensions or [])
        
        return {
            "status": "success",
            "is_installed": is_installed,
            "name": ext.name,
            "description": ext.description,
            "requires_compilation": ext.requires_compilation
        }
        
    except Exception as e:
        error(f"❌ Error checking extension status: {e}")
        return {"status": "error", "message": str(e)}
"""
PHP extensions management functionality.

This module provides functions for installing, uninstalling, and managing
PHP extensions for websites.
"""

from typing import Dict, List, Any, Optional, Type

from src.common.logging import log_call, info, warn, error, success, debug
from src.features.website.utils import get_site_config
from src.features.php.extensions.registry import (
    get_extension_instance,
    get_extension_list,
    EXTENSION_REGISTRY
)


@log_call
def install_php_extension(domain: str, extension_id: str) -> bool:
    """
    Install a PHP extension for a website.
    
    Args:
        domain: Website domain name
        extension_id: Extension identifier
        
    Returns:
        bool: True if installation was successful, False otherwise
    """
    try:
        ext = get_extension_instance(extension_id)
        success = ext.install(domain)
        if success:
            ext.update_config(domain)
            ext.post_install(domain)
            info(f"✅ {ext.name} extension installed successfully for {domain}")
        return success
    except Exception as e:
        error(f"❌ Error installing PHP extension: {e}")
        return False


@log_call
def uninstall_php_extension(domain: str, extension_id: str) -> bool:
    """
    Uninstall a PHP extension from a website.
    
    Args:
        domain: Website domain name
        extension_id: Extension identifier
        
    Returns:
        bool: True if uninstallation was successful, False otherwise
    """
    try:
        ext = get_extension_instance(extension_id)
        success = ext.uninstall(domain)
        if success:
            ext.remove_from_config(domain)
            info(f"✅ {ext.name} extension uninstalled successfully from {domain}")
        return success
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
    site_config = get_site_config(domain)
    if not site_config or not hasattr(site_config, 'php') or not site_config.php:
        return []
    
    installed_ids = site_config.php.php_installed_extensions or []
    result = []
    
    for ext_id in installed_ids:
        try:
            if ext_id in EXTENSION_REGISTRY:
                ext = get_extension_instance(ext_id)
                result.append({
                    "id": ext.id,
                    "name": ext.name,
                    "description": ext.description
                })
            else:
                # Extension in config but not in registry
                result.append({
                    "id": ext_id,
                    "name": f"Unknown ({ext_id})",
                    "description": "Extension registered in configuration but implementation not found"
                })
        except Exception:
            pass
    
    return result


@log_call
def get_available_extensions(domain: str) -> List[Dict[str, Any]]:
    """
    Get a list of available PHP extensions for a website.
    
    Args:
        domain: Website domain name
        
    Returns:
        List[Dict[str, Any]]: List of available extensions with metadata
    """
    # Get PHP version for compatibility check
    site_config = get_site_config(domain)
    php_version = site_config.php.php_version if site_config and hasattr(site_config, 'php') and site_config.php else None
    
    # Get installed extensions
    installed_ids = []
    if site_config and hasattr(site_config, 'php') and site_config.php:
        installed_ids = site_config.php.php_installed_extensions or []
    
    # Get all available extensions
    all_extensions = get_extension_list()
    result = []
    
    # Debug information
    info(f"Available PHP extensions in registry: {list(all_extensions.keys())}")
    info(f"Current PHP version: {php_version}")
    info(f"Already installed extensions: {installed_ids}")
    
    if not all_extensions:
        warn("No extensions are registered in the system. This is unexpected.")
        # Add a default IonCube entry as fallback
        try:
            from src.features.php.extensions.ioncube_loader import IoncubeLoaderExtension
            ext = IoncubeLoaderExtension()
            result.append({
                "id": ext.id,
                "name": ext.name,
                "description": ext.description,
                "requires_compilation": ext.requires_compilation
            })
        except Exception as e:
            error(f"Failed to add fallback IonCube entry: {e}")
    
    for ext_id, ext_class in all_extensions.items():
        # Skip already installed extensions
        if ext_id in installed_ids:
            debug(f"Skipping {ext_id} as it's already installed")
            continue
            
        try:
            ext = ext_class()
            
            # Check PHP version compatibility if version is known
            if php_version and not ext.check_compatibility(php_version):
                info(f"Skipping {ext_id} as it's not compatible with PHP {php_version}")
                continue
                
            info(f"Adding {ext_id} to available extensions")
            result.append({
                "id": ext.id,
                "name": ext.name,
                "description": ext.description,
                "requires_compilation": ext.requires_compilation
            })
        except Exception as e:
            error(f"Error processing extension {ext_id}: {e}")
    
    # If no extensions are available after compatibility checks, add IonCube anyway with a note
    if not result and php_version and php_version != "8.3":
        try:
            from src.features.php.extensions.ioncube_loader import IoncubeLoaderExtension
            ext = IoncubeLoaderExtension()
            result.append({
                "id": ext.id,
                "name": ext.name,
                "description": f"{ext.description} (Force-added as fallback)",
                "requires_compilation": ext.requires_compilation
            })
            warn("Force-adding IonCube Loader as no other extensions were available")
        except Exception as e:
            error(f"Failed to add fallback IonCube entry: {e}")
    
    return result
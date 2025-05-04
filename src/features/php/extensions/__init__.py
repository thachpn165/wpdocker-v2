"""
PHP extensions management functionality.

This package provides functionality for installing, uninstalling, and managing
PHP extensions for websites.
"""

from src.features.php.extensions.base import BaseExtension
from src.features.php.extensions.registry import (
    register_extension,
    get_extension_instance,
    get_extension_list,
    EXTENSION_REGISTRY
)
from src.features.php.extensions.manager import (
    install_php_extension,
    uninstall_php_extension,
    get_installed_extensions,
    get_available_extensions
)

# Register all available extensions
from src.features.php.extensions.ioncube_loader import IoncubeLoaderExtension

__all__ = [
    # Base classes
    'BaseExtension',
    
    # Registry
    'register_extension',
    'get_extension_instance',
    'get_extension_list',
    'EXTENSION_REGISTRY',
    
    # Management
    'install_php_extension',
    'uninstall_php_extension',
    'get_installed_extensions',
    'get_available_extensions',
    
    # Extensions
    'IoncubeLoaderExtension'
]
"""
PHP extension registry.

This module provides a registry of available PHP extensions and
functions for retrieving extension implementations.
"""

from typing import Dict, Any, Type, Optional

from src.common.logging import debug, error


# Extension registry will be populated by extension classes that inherit from BaseExtension
EXTENSION_REGISTRY = {}


def register_extension(extension_id: str, extension_class: Type) -> None:
    """
    Register a PHP extension in the extension registry.
    
    Args:
        extension_id: Unique identifier for the extension
        extension_class: Class implementing the extension
    """
    global EXTENSION_REGISTRY
    EXTENSION_REGISTRY[extension_id] = extension_class
    debug(f"📋 Registered PHP extension: {extension_id}")


def get_extension_instance(extension_id: str) -> Optional[Any]:
    """
    Get an instance of a PHP extension by ID.
    
    Args:
        extension_id: Unique identifier for the extension
        
    Returns:
        Extension instance or None if not found
        
    Raises:
        ValueError: If extension_id is not in the registry
    """
    if extension_id not in EXTENSION_REGISTRY:
        error(f"❌ PHP extension '{extension_id}' not found in registry")
        raise ValueError(f"PHP extension '{extension_id}' not found in registry")
    
    extension_class = EXTENSION_REGISTRY[extension_id]
    return extension_class()


def get_extension_list() -> Dict[str, Type]:
    """
    Get a dictionary of all registered PHP extensions.
    
    Returns:
        Dict mapping extension IDs to extension classes
    """
    return EXTENSION_REGISTRY.copy()
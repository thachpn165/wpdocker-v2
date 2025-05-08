"""
NGINX cache management module.

This module provides functionality for managing different types of NGINX cache
configurations for websites.
"""

from src.features.nginx.cache.cache_manager import (
    install_cache,
    get_available_cache_types
)

__all__ = [
    'install_cache',
    'get_available_cache_types'
]
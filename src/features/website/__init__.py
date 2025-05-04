"""
Website management functionality.

This package provides functionality for managing websites,
including creating, deleting, and configuring websites.
"""

# Core utility functions
from src.features.website.utils import (
    website_list,
    is_website_exists,
    is_website_running,
    get_site_config,
    set_site_config,
    delete_site_config,
    select_website,
    get_sites_dir,
    calculate_php_fpm_values
)

# Site management operations
from src.features.website.manager import (
    create_website,
    delete_website,
    restart_website
)

# CLI interfaces
from src.features.website.cli import (
    cli_create_website,
    cli_delete_website,
    cli_restart_website,
    cli_website_info,
    cli_list_websites,
    cli_view_logs
)

__all__ = [
    # Core utilities
    'website_list',
    'is_website_exists',
    'is_website_running',
    'get_site_config',
    'set_site_config',
    'delete_site_config',
    'select_website',
    'get_sites_dir',
    'calculate_php_fpm_values',
    
    # Manager operations
    'create_website',
    'delete_website',
    'restart_website',
    
    # CLI interfaces
    'cli_create_website',
    'cli_delete_website',
    'cli_restart_website',
    'cli_website_info',
    'cli_list_websites',
    'cli_view_logs'
]
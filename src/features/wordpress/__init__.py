"""
WordPress management functionality.

This package provides functionality for managing WordPress installations,
including installation, configuration, and plugin/theme management.
"""

# Core utilities
from src.features.wordpress.utils import run_wp_cli, get_php_container_name

# Installation and management
from src.features.wordpress.installer import install_wordpress, uninstall_wordpress
from src.features.wordpress.actions import (
    download_core,
    configure_db,
    core_install,
    fix_permissions,
    verify_installation
)

# CLI interfaces
from src.features.wordpress.cli import (
    cli_install_wordpress,
    cli_run_wp_command,
    cli_uninstall_wordpress
)

__all__ = [
    # Core utilities
    'run_wp_cli',
    'get_php_container_name',
    
    # Installation and management
    'install_wordpress',
    'uninstall_wordpress',
    'download_core',
    'configure_db',
    'core_install',
    'fix_permissions',
    'verify_installation',
    
    # CLI interfaces
    'cli_install_wordpress',
    'cli_run_wp_command',
    'cli_uninstall_wordpress'
]
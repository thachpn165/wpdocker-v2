"""
PHP management functionality.

This package provides functionality for managing PHP installations,
including version selection, configuration, and extension management.
"""

# Core utilities
from src.features.php.utils import (
    get_php_container_id_by_name,
    get_php_container_id,
    get_php_container_name,
    php_choose_version,
    AVAILABLE_PHP_VERSIONS
)

# Container client
from src.features.php.client import (
    init_php_client,
    run_php_command,
    run_php_script
)

# Version management
from src.features.php.version import (
    change_php_version,
    get_current_php_version,
    restore_php_extensions
)

# Configuration management
from src.features.php.config import (
    edit_php_ini,
    edit_php_fpm_pool,
    backup_php_config,
    restore_php_config_backup
)

# Extensions management
from src.features.php.extensions import (
    install_php_extension,
    uninstall_php_extension,
    get_installed_extensions,
    get_available_extensions,
    BaseExtension
)

# CLI interfaces
from src.features.php.cli import (
    cli_change_php_version,
    cli_edit_php_config,
    cli_list_extensions,
    cli_install_extension,
    cli_uninstall_extension
)

__all__ = [
    # Core utilities
    'get_php_container_id_by_name',
    'get_php_container_id',
    'get_php_container_name',
    'php_choose_version',
    'AVAILABLE_PHP_VERSIONS',
    
    # Container client
    'init_php_client',
    'run_php_command',
    'run_php_script',
    
    # Version management
    'change_php_version',
    'get_current_php_version',
    'restore_php_extensions',
    
    # Configuration management
    'edit_php_ini',
    'edit_php_fpm_pool',
    'backup_php_config',
    'restore_php_config_backup',
    
    # Extensions management
    'install_php_extension',
    'uninstall_php_extension',
    'get_installed_extensions',
    'get_available_extensions',
    'BaseExtension',
    
    # CLI interfaces
    'cli_change_php_version',
    'cli_edit_php_config',
    'cli_list_extensions',
    'cli_install_extension',
    'cli_uninstall_extension'
]
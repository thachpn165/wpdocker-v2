"""
CLI interfaces for PHP management.

This package provides command-line interfaces for managing PHP,
including version changes, configuration editing, and extensions management.
"""

from src.features.php.cli.version import cli_change_php_version
from src.features.php.cli.config_editor import cli_edit_php_config
from src.features.php.cli.extensions import (
    cli_list_extensions,
    cli_install_extension,
    cli_uninstall_extension
)
from src.features.php.cli.main import main

__all__ = [
    'cli_change_php_version',
    'cli_edit_php_config',
    'cli_list_extensions',
    'cli_install_extension',
    'cli_uninstall_extension',
    'main'
]
"""
CLI interfaces for WordPress management.

This package provides command-line interfaces for installing, managing,
and uninstalling WordPress installations.
"""

from src.features.wordpress.cli.install import cli_install_wordpress
from src.features.wordpress.cli.manage import cli_run_wp_command, cli_uninstall_wordpress
from src.features.wordpress.cli.main import main

__all__ = [
    'cli_install_wordpress',
    'cli_run_wp_command',
    'cli_uninstall_wordpress',
    'main'
]
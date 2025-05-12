"""
System CLI module initialization.

This module exports the CLI commands and functions for the system tools.
"""

from src.features.system.cli.main import system_cli
from src.features.system.cli.system_info import view_system_info_cli
from src.features.system.cli.rebuild import rebuild_core_cli
from src.features.system.cli.change_language import cli_change_language, change_language_cli


__all__ = [
    'system_cli',
    'view_system_info_cli',
    'rebuild_core_cli',
    'cli_change_language',
    'change_language_cli'
]

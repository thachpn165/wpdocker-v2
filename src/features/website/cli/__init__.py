"""
CLI interfaces for website management.

This package provides command-line interfaces for managing websites,
including creation, deletion, restart, information display, and log viewing.
"""

from src.features.website.cli.create import cli_create_website
from src.features.website.cli.delete import cli_delete_website
from src.features.website.cli.restart import cli_restart_website
from src.features.website.cli.info import cli_website_info, get_website_info
from src.features.website.cli.list import cli_list_websites, list_websites
from src.features.website.cli.logs import cli_view_logs

__all__ = [
    'cli_create_website',
    'cli_delete_website',
    'cli_restart_website',
    'cli_website_info',
    'get_website_info',
    'cli_list_websites',
    'list_websites',
    'cli_view_logs'
]
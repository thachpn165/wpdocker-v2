"""
Main CLI module for NGINX operations.

This module provides the command-line interface for NGINX management
with commands for testing configurations, reloading, restarting,
and managing cache settings.
"""

import click
from typing import Optional, List

from src.common.logging import info, error, debug


@click.group(name="nginx")
def nginx_cli():
    """NGINX management commands."""
    pass


# Import subcommands
from src.features.nginx.cli.config import test_config_cli
from src.features.nginx.cli.reload import reload_cli
from src.features.nginx.cli.restart import restart_cli
from src.features.nginx.cli.cache import cache_cli

# Add subcommands to the main group
nginx_cli.add_command(test_config_cli)
nginx_cli.add_command(reload_cli)
nginx_cli.add_command(restart_cli)
nginx_cli.add_command(cache_cli)


if __name__ == "__main__":
    nginx_cli()
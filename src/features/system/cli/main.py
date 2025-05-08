"""
System CLI main module.

This module provides the main CLI command group for system management.
"""

import click
from typing import Optional

from src.common.logging import info, error, debug, success

@click.group()
def system_cli():
    """System management and information tools."""
    pass

# Import subcommands
from src.features.system.cli.containers import (
    container_cli
)

# Add subcommands to the main group
system_cli.add_command(container_cli)

if __name__ == "__main__":
    system_cli()
"""
System CLI main module.

This module provides the main CLI command group for system management.
"""


import click
from src.features.system.cli.rebuild import rebuild_core_cli
from src.features.system.cli.system_info import view_system_info_cli
from src.features.system.cli.change_language import change_language_cli

from src.common.logging import info, error, debug, success


@click.group("system")
def system_cli():
    """System management commands."""
    pass


# Add subcommands to the main group
system_cli.add_command(rebuild_core_cli)
system_cli.add_command(view_system_info_cli)
system_cli.add_command(change_language_cli)

if __name__ == "__main__":
    system_cli()

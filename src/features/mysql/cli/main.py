"""
Main CLI entry point for MySQL database management.

This module provides a centralized command-line interface for all MySQL
database management operations, including subcommands for various actions.
"""

import sys
import argparse
from typing import List, Optional

from src.common.logging import log_call, info, warn, error, success
from src.features.mysql.cli.restore import cli_restore_database
from src.features.mysql.cli.config_editor import cli_mysql_config


@log_call
def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command-line arguments for the MySQL CLI.
    
    Args:
        args: Command-line arguments
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="MySQL database management CLI",
        prog="mysql"
    )
    
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="MySQL management commands"
    )
    
    # Restore database
    restore_parser = subparsers.add_parser(
        "restore",
        help="Restore a database from backup"
    )
    
    # Edit configuration
    config_parser = subparsers.add_parser(
        "config",
        help="Manage MySQL configuration"
    )
    
    return parser.parse_args(args)


@log_call
def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the MySQL CLI.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    if args is None:
        args = sys.argv[1:]
    
    parsed_args = parse_args(args)
    
    if not parsed_args.command:
        # No command specified, show help
        parse_args(["--help"])
        return 1
    
    if parsed_args.command == "restore":
        return 0 if cli_restore_database() else 1
    
    elif parsed_args.command == "config":
        return 0 if cli_mysql_config() else 1
    
    else:
        error(f"Unknown command: {parsed_args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
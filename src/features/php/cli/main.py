"""
Main CLI entry point for PHP management.

This module provides a centralized command-line interface for all PHP
management operations, including version changes, configuration editing,
and extensions management.
"""

import sys
import argparse
from typing import List, Optional

from src.common.logging import log_call, info, warn, error, success
from src.features.php.cli.version import cli_change_php_version
from src.features.php.cli.config_editor import cli_edit_php_config
from src.features.php.cli.extensions import (
    cli_list_extensions,
    cli_install_extension,
    cli_uninstall_extension
)


@log_call
def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command-line arguments for the PHP CLI.
    
    Args:
        args: Command-line arguments
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="PHP management CLI",
        prog="php"
    )
    
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="PHP management commands"
    )
    
    # Version command
    version_parser = subparsers.add_parser(
        "version",
        help="Change PHP version for a website"
    )
    
    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Edit PHP configuration files"
    )
    
    # Extensions command
    ext_parser = subparsers.add_parser(
        "extension",
        help="Manage PHP extensions"
    )
    ext_subparsers = ext_parser.add_subparsers(
        title="actions",
        dest="action",
        help="Extension management actions"
    )
    
    # Extension list
    ext_list_parser = ext_subparsers.add_parser(
        "list",
        help="List installed and available PHP extensions"
    )
    
    # Extension install
    ext_install_parser = ext_subparsers.add_parser(
        "install",
        help="Install a PHP extension"
    )
    
    # Extension uninstall
    ext_uninstall_parser = ext_subparsers.add_parser(
        "uninstall",
        help="Uninstall a PHP extension"
    )
    
    return parser.parse_args(args)


@log_call
def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the PHP CLI.
    
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
    
    if parsed_args.command == "version":
        return 0 if cli_change_php_version() else 1
    
    elif parsed_args.command == "config":
        return 0 if cli_edit_php_config() else 1
    
    elif parsed_args.command == "extension":
        if not hasattr(parsed_args, "action") or not parsed_args.action:
            # Default to list if no action specified
            return 0 if cli_list_extensions() else 1
        
        if parsed_args.action == "list":
            return 0 if cli_list_extensions() else 1
        
        elif parsed_args.action == "install":
            return 0 if cli_install_extension() else 1
        
        elif parsed_args.action == "uninstall":
            return 0 if cli_uninstall_extension() else 1
        
        else:
            error(f"Unknown extension action: {parsed_args.action}")
            return 1
    
    else:
        error(f"Unknown command: {parsed_args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
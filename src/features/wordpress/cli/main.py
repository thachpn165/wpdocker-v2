"""
Main CLI entry point for WordPress management.

This module provides a centralized command-line interface for all WordPress
management operations, including installation and command execution.
"""

import sys
import argparse
from typing import List, Optional

from src.common.logging import log_call, info, warn, error, success
from src.features.wordpress.cli.install import cli_install_wordpress
from src.features.wordpress.cli.manage import cli_run_wp_command, cli_uninstall_wordpress


@log_call
def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command-line arguments for the WordPress CLI.
    
    Args:
        args: Command-line arguments
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="WordPress management CLI",
        prog="wordpress"
    )
    
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="WordPress management commands"
    )
    
    # Install WordPress
    install_parser = subparsers.add_parser(
        "install",
        help="Install WordPress on a website"
    )
    
    # Run WP-CLI command
    wp_parser = subparsers.add_parser(
        "wp",
        help="Run WP-CLI commands"
    )
    
    # Uninstall WordPress
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Completely remove WordPress from a website"
    )
    
    return parser.parse_args(args)


@log_call
def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the WordPress CLI.
    
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
    
    if parsed_args.command == "install":
        return 0 if cli_install_wordpress() else 1
    
    elif parsed_args.command == "wp":
        return 0 if cli_run_wp_command() else 1
    
    elif parsed_args.command == "uninstall":
        return 0 if cli_uninstall_wordpress() else 1
    
    else:
        error(f"Unknown command: {parsed_args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
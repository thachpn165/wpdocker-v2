"""
Main CLI entry point for SSL certificate management.

This module provides a centralized command-line interface for all SSL
certificate management operations, including installation, checking, and editing.
"""

import sys
import argparse
from typing import List, Optional

from src.common.logging import log_call, info, warn, error, success
from src.features.ssl.cli.install import cli_install_ssl
from src.features.ssl.cli.check import cli_check_ssl
from src.features.ssl.cli.edit import cli_edit_ssl


@log_call
def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command-line arguments for the SSL CLI.
    
    Args:
        args: Command-line arguments
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="SSL certificate management CLI",
        prog="ssl"
    )
    
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="SSL management commands"
    )
    
    # Install SSL certificate
    install_parser = subparsers.add_parser(
        "install",
        help="Install SSL certificate on a website"
    )
    
    # Check SSL certificate
    check_parser = subparsers.add_parser(
        "check",
        help="Check SSL certificate information"
    )
    check_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    
    # Edit SSL certificate
    edit_parser = subparsers.add_parser(
        "edit",
        help="Edit SSL certificate files"
    )
    
    return parser.parse_args(args)


@log_call
def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the SSL CLI.
    
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
        return 0 if cli_install_ssl() else 1
    
    elif parsed_args.command == "check":
        return 0 if cli_check_ssl(parsed_args.json if hasattr(parsed_args, "json") else False) else 1
    
    elif parsed_args.command == "edit":
        return 0 if cli_edit_ssl() else 1
    
    else:
        error(f"Unknown command: {parsed_args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
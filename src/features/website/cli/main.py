"""
Main CLI entry point for website management.

This module provides a centralized command-line interface for all website
management operations, including subcommands for various actions.
"""

import sys
import argparse
from typing import List, Optional

from src.common.logging import log_call, info, warn, error, success
from src.features.website.cli import (
    cli_create_website,
    cli_delete_website,
    cli_restart_website,
    cli_website_info,
    cli_list_websites,
    cli_view_logs
)


@log_call
def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command-line arguments for the website CLI.
    
    Args:
        args: Command-line arguments
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Website management CLI",
        prog="website"
    )
    
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="Website management commands"
    )
    
    # Create website
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new website"
    )
    
    # Delete website
    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete an existing website"
    )
    
    # Restart website
    restart_parser = subparsers.add_parser(
        "restart",
        help="Restart a website"
    )
    
    # Website info
    info_parser = subparsers.add_parser(
        "info",
        help="Display website information"
    )
    info_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    
    # List websites
    list_parser = subparsers.add_parser(
        "list",
        help="List all websites"
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )
    
    # View logs
    logs_parser = subparsers.add_parser(
        "logs",
        help="View website logs"
    )
    
    return parser.parse_args(args)


@log_call
def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the website CLI.
    
    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    if args is None:
        args = sys.argv[1:]
    
    parsed_args = parse_args(args)
    
    if not parsed_args.command:
        # No command specified, default to list
        return 0 if cli_list_websites() else 1
    
    if parsed_args.command == "create":
        return 0 if cli_create_website() else 1
    
    elif parsed_args.command == "delete":
        return 0 if cli_delete_website() else 1
    
    elif parsed_args.command == "restart":
        return 0 if cli_restart_website() else 1
    
    elif parsed_args.command == "info":
        return 0 if cli_website_info(parsed_args.json if hasattr(parsed_args, "json") else False) else 1
    
    elif parsed_args.command == "list":
        return 0 if cli_list_websites() else 1
    
    elif parsed_args.command == "logs":
        return 0 if cli_view_logs() else 1
    
    else:
        error(f"Unknown command: {parsed_args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
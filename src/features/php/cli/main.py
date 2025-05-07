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


def create_parser() -> argparse.ArgumentParser:
    """
    Create the main argument parser for PHP CLI.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="PHP management CLI",
        prog="php",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  php version change example.com 8.2    # Change PHP version to 8.2
  php config edit example.com           # Edit PHP configuration
  php extension list example.com        # List installed extensions
  php extension install example.com ioncube  # Install IonCube extension
        """
    )
    
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="PHP management commands"
    )
    
    # Version command
    version_parser = subparsers.add_parser(
        "version",
        help="Manage PHP versions",
        description="Change or check PHP versions for websites"
    )
    version_subparsers = version_parser.add_subparsers(
        title="actions",
        dest="action",
        help="Version management actions"
    )
    
    # Version change
    version_change_parser = version_subparsers.add_parser(
        "change",
        help="Change PHP version for a website"
    )
    version_change_parser.add_argument(
        "domain",
        help="Website domain name"
    )
    version_change_parser.add_argument(
        "version",
        help="PHP version to change to (e.g., 8.2)"
    )
    
    # Version check
    version_check_parser = version_subparsers.add_parser(
        "check",
        help="Check current PHP version"
    )
    version_check_parser.add_argument(
        "domain",
        help="Website domain name"
    )
    
    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Manage PHP configuration",
        description="Edit or view PHP configuration files"
    )
    config_subparsers = config_parser.add_subparsers(
        title="actions",
        dest="action",
        help="Configuration management actions"
    )
    
    # Config edit
    config_edit_parser = config_subparsers.add_parser(
        "edit",
        help="Edit PHP configuration files"
    )
    config_edit_parser.add_argument(
        "domain",
        help="Website domain name"
    )
    config_edit_parser.add_argument(
        "--type",
        choices=["ini", "fpm"],
        default="ini",
        help="Configuration file type to edit (default: ini)"
    )
    
    # Config view
    config_view_parser = config_subparsers.add_parser(
        "view",
        help="View PHP configuration files"
    )
    config_view_parser.add_argument(
        "domain",
        help="Website domain name"
    )
    config_view_parser.add_argument(
        "--type",
        choices=["ini", "fpm"],
        default="ini",
        help="Configuration file type to view (default: ini)"
    )
    
    # Extensions command
    ext_parser = subparsers.add_parser(
        "extension",
        help="Manage PHP extensions",
        description="Install, uninstall, or list PHP extensions"
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
    ext_list_parser.add_argument(
        "domain",
        help="Website domain name"
    )
    ext_list_parser.add_argument(
        "--available",
        action="store_true",
        help="Show available extensions instead of installed ones"
    )
    
    # Extension install
    ext_install_parser = ext_subparsers.add_parser(
        "install",
        help="Install a PHP extension"
    )
    ext_install_parser.add_argument(
        "domain",
        help="Website domain name"
    )
    ext_install_parser.add_argument(
        "extension",
        help="Extension identifier to install"
    )
    
    # Extension uninstall
    ext_uninstall_parser = ext_subparsers.add_parser(
        "uninstall",
        help="Uninstall a PHP extension"
    )
    ext_uninstall_parser.add_argument(
        "domain",
        help="Website domain name"
    )
    ext_uninstall_parser.add_argument(
        "extension",
        help="Extension identifier to uninstall"
    )
    
    return parser


@log_call
def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command-line arguments for the PHP CLI.
    
    Args:
        args: Command-line arguments
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = create_parser()
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
    
    try:
        parsed_args = parse_args(args)
        
        if not parsed_args.command:
            # No command specified, show help
            create_parser().print_help()
            return 1
            
        # Handle version commands
        if parsed_args.command == "version":
            if parsed_args.action == "change":
                return 0 if cli_change_php_version(parsed_args.domain, parsed_args.version) else 1
            elif parsed_args.action == "check":
                from src.features.php.version import get_current_php_version
                version = get_current_php_version(parsed_args.domain)
                if version:
                    info(f"Current PHP version for {parsed_args.domain}: {version}")
                    return 0
                return 1
                
        # Handle config commands
        elif parsed_args.command == "config":
            if parsed_args.action == "edit":
                return 0 if cli_edit_php_config(parsed_args.domain, parsed_args.type) else 1
            elif parsed_args.action == "view":
                from src.features.php.config import view_php_config
                return 0 if view_php_config(parsed_args.domain, parsed_args.type) else 1
                
        # Handle extension commands
        elif parsed_args.command == "extension":
            if parsed_args.action == "list":
                return 0 if cli_list_extensions(parsed_args.domain, parsed_args.available) else 1
            elif parsed_args.action == "install":
                return 0 if cli_install_extension(parsed_args.domain, parsed_args.extension) else 1
            elif parsed_args.action == "uninstall":
                return 0 if cli_uninstall_extension(parsed_args.domain, parsed_args.extension) else 1
                
        else:
            error(f"Unknown command: {parsed_args.command}")
            return 1
            
    except KeyboardInterrupt:
        info("\nOperation cancelled by user")
        return 1
    except Exception as e:
        error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
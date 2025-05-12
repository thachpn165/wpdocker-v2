"""
Main CLI entry point for update management.

This module provides the main command-line interface for checking
and applying updates to the WP Docker application.
"""

import sys
import argparse
from typing import List, Optional

from src.common.logging import log_call, info, error, success, warn
from src.features.update.actions import check_version_action, update_action


@log_call
def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: Command-line arguments
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="WP Docker update management",
        prog="update"
    )
    
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="Update commands"
    )
    
    # Check for updates
    check_parser = subparsers.add_parser(
        "check",
        help="Check for updates"
    )
    
    # Apply updates
    update_parser = subparsers.add_parser(
        "update",
        help="Update to the latest version"
    )
    
    return parser.parse_args(args)


@log_call
def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the update CLI.
    
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
        
    if parsed_args.command == "check":
        return cli_check_version()
    elif parsed_args.command == "update":
        return cli_update()
    else:
        error(f"Unknown command: {parsed_args.command}")
        return 1


@log_call
def cli_check_version() -> int:
    """
    Check for updates from the command line.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        result = check_version_action()
        
        info(f"Current version: {result['current_version']} ({result['channel']})")
        
        if result["update_available"]:
            update_info = result["update_info"]
            version = update_info.get("version", "unknown")
            success(f"New version available: {version}")
            
            # Show release notes if available
            if "notes" in update_info and update_info["notes"]:
                info(f"Release notes: {update_info['notes']}")
                
            return 0
        else:
            info("You are using the latest version")
            return 0
            
    except Exception as e:
        error(f"Error checking for updates: {str(e)}")
        return 1


@log_call
def cli_update() -> int:
    """
    Apply updates from the command line.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # First check if updates are available
        check_result = check_version_action()
        
        if not check_result["update_available"]:
            info("You are already using the latest version")
            return 0
            
        # Show what will be updated
        update_info = check_result["update_info"]
        current_version = check_result["current_version"]
        new_version = update_info.get("version", "unknown")
        
        info(f"Updating from {current_version} to {new_version}...")
        
        # Apply the update
        result = update_action()
        
        if result["success"]:
            success(f"Successfully updated to version {new_version}")
            return 0
        else:
            error(f"Update failed: {result['message']}")
            return 1
            
    except Exception as e:
        error(f"Error during update: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
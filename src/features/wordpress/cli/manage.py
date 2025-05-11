"""
CLI interface for WordPress management.

This module provides a command-line interface for managing WordPress installations,
including running WP-CLI commands and performing common administrative tasks.
"""

import sys
from questionary import text, select, confirm
from typing import Optional, Dict, Any, List

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import select_website
from src.features.wordpress.utils import run_wp_cli
from src.features.wordpress.installer import uninstall_wordpress


@log_call
def get_wp_cli_command_params() -> Optional[Dict[str, Any]]:
    """
    Prompt the user for a WP-CLI command to run.

    Returns:
        Optional[Dict[str, Any]]: Dictionary with domain and command if successful,
                                 None if cancelled
    """
    try:
        # Select website
        domain = select_website("Select WordPress website:")
        if not domain:
            warn("No website selected or no websites available.")
            return None

        # Common WP-CLI commands
        common_commands = [
            "Custom command...",
            "wp core version",
            "wp plugin list",
            "wp theme list",
            "wp user list",
            "wp db check",
            "wp cache flush",
            "wp option list",
            "wp rewrite flush --hard",
            "wp core update",
            "wp plugin update --all",
            "wp theme update --all"
        ]

        selected = select(
            "Select WordPress command:",
            choices=common_commands
        ).ask()

        if not selected:
            return None

        if selected == "Custom command...":
            custom_command = text(
                "Enter WP-CLI command (without 'wp' prefix):"
            ).ask()

            if not custom_command:
                return None

            command = custom_command
        else:
            command = selected.replace("wp ", "")

        return {
            "domain": domain,
            "command": command
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_run_wp_command() -> bool:
    """
    CLI entry point for running WP-CLI commands.

    Returns:
        bool: True if command execution was successful, False otherwise
    """
    params = get_wp_cli_command_params()
    if not params:
        return False

    domain = params["domain"]
    command = params["command"]

    # Split command into list of arguments
    args = command.split()

    result = run_wp_cli(domain, args)
    if result is not None:
        print("\nCommand output:")
        print("---------------")
        print(result)
        return True
    else:
        error(f"❌ Command failed: wp {command}")
        return False


@log_call
def get_uninstall_wordpress_params() -> Optional[Dict[str, Any]]:
    """
    Prompt the user to uninstall WordPress from a website.

    Returns:
        Optional[Dict[str, Any]]: Dictionary with domain if successful,
                                 None if cancelled
    """
    try:
        # Select website
        domain = select_website("Select WordPress website to uninstall:")
        if not domain:
            warn("No website selected or no websites available.")
            return None

        # Confirm uninstallation
        confirm_msg = f"⚠️ Are you sure you want to UNINSTALL WordPress from {domain}? "
        confirm_msg += "This will DELETE all WordPress files, database content, and configuration."
        if not confirm(confirm_msg).ask():
            warn("WordPress uninstallation cancelled.")
            return None

        # Double-confirm
        if not confirm("⚠️ FINAL WARNING: This action cannot be undone! Continue?").ask():
            warn("WordPress uninstallation cancelled.")
            return None

        return {
            "domain": domain
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_uninstall_wordpress() -> bool:
    """
    CLI entry point for WordPress uninstallation.

    Returns:
        bool: True if uninstallation was successful, False otherwise
    """
    params = get_uninstall_wordpress_params()
    if not params:
        return False

    return uninstall_wordpress(params["domain"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        success = cli_uninstall_wordpress()
    else:
        success = cli_run_wp_command()
    
    sys.exit(0 if success else 1)
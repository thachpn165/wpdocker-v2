"""
CLI interface for PHP extensions management.

This module provides a command-line interface for installing, uninstalling,
and listing PHP extensions for websites.
"""

import sys
import json
from questionary import select, confirm
from typing import Optional, Dict, Any, List

from rich.console import Console
from rich.table import Table

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import select_website
from src.features.php.extensions.manager import (
    install_php_extension,
    uninstall_php_extension,
    get_installed_extensions,
    get_available_extensions
)

# Force extensions to be registered
import src.features.php.extensions.force_registry


# Create a console instance for rich output
console = Console()


@log_call
def display_extensions_table(extensions: List[Dict[str, Any]], title: str) -> None:
    """
    Display a table of PHP extensions.
    
    Args:
        extensions: List of extension dictionaries
        title: Table title
    """
    if not extensions:
        info("No extensions found.")
        return
    
    table = Table(title=title, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold green")
    table.add_column("Description", style="white")
    
    for ext in extensions:
        table.add_row(ext["id"], ext["name"], ext["description"])
    
    console.print(table)


@log_call
def get_extension_install_params() -> Optional[Dict[str, Any]]:
    """
    Prompt the user for extension installation parameters.

    Returns:
        Optional[Dict[str, Any]]: Dictionary with domain and extension_id if successful,
                                 None if cancelled
    """
    try:
        # Select website
        domain = select_website("Select website to install PHP extension for:")

        if not domain:
            warn("No website selected or no websites available.")
            return None

        # Get available extensions
        available_extensions = get_available_extensions(domain)
        if not available_extensions:
            error("No available extensions found for this website.")
            return None

        # Create choices for questionary
        choices = [
            {
                "name": f"{ext['name']} - {ext['description']}",
                "value": ext["id"]
            }
            for ext in available_extensions
        ]

        # Select extension
        extension_id = select(
            "Select PHP extension to install:",
            choices=choices
        ).ask()

        if not extension_id:
            return None

        # Get extension name for confirmation
        extension_name = next(
            (ext["name"] for ext in available_extensions if ext["id"] == extension_id),
            extension_id
        )

        # Confirm installation
        confirm_install = confirm(
            f"Install {extension_name} for {domain}?"
        ).ask()

        if not confirm_install:
            warn("Extension installation cancelled.")
            return None

        return {
            "domain": domain,
            "extension_id": extension_id
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def get_extension_uninstall_params() -> Optional[Dict[str, Any]]:
    """
    Prompt the user for extension uninstallation parameters.

    Returns:
        Optional[Dict[str, Any]]: Dictionary with domain and extension_id if successful,
                                 None if cancelled
    """
    try:
        # Select website
        domain = select_website("Select website to uninstall PHP extension from:")

        if not domain:
            warn("No website selected or no websites available.")
            return None

        # Get installed extensions
        installed_extensions = get_installed_extensions(domain)
        if not installed_extensions:
            error("No installed extensions found for this website.")
            return None

        # Create choices for questionary
        choices = [
            {
                "name": f"{ext['name']} - {ext['description']}",
                "value": ext["id"]
            }
            for ext in installed_extensions
        ]

        # Select extension
        extension_id = select(
            "Select PHP extension to uninstall:",
            choices=choices
        ).ask()

        if not extension_id:
            return None

        # Get extension name for confirmation
        extension_name = next(
            (ext["name"] for ext in installed_extensions if ext["id"] == extension_id),
            extension_id
        )

        # Confirm uninstallation
        confirm_uninstall = confirm(
            f"Uninstall {extension_name} from {domain}?"
        ).ask()

        if not confirm_uninstall:
            warn("Extension uninstallation cancelled.")
            return None

        return {
            "domain": domain,
            "extension_id": extension_id
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_list_extensions() -> bool:
    """
    CLI entry point for listing PHP extensions.
    
    Returns:
        bool: True if listing was successful, False otherwise
    """
    domain = select_website("Select website to list PHP extensions for:")
    
    if not domain:
        warn("No website selected or no websites available.")
        return False
    
    # Get installed extensions
    installed_extensions = get_installed_extensions(domain)
    display_extensions_table(
        installed_extensions,
        f"🔌 Installed PHP Extensions for {domain}"
    )
    
    # Get available extensions
    available_extensions = get_available_extensions(domain)
    display_extensions_table(
        available_extensions,
        f"📦 Available PHP Extensions for {domain}"
    )
    
    return True


@log_call
def cli_install_extension() -> bool:
    """
    CLI entry point for installing PHP extensions.

    Returns:
        bool: True if installation was successful, False otherwise
    """
    params = get_extension_install_params()
    if not params:
        return False

    return install_php_extension(params["domain"], params["extension_id"])


@log_call
def cli_uninstall_extension() -> bool:
    """
    CLI entry point for uninstalling PHP extensions.

    Returns:
        bool: True if uninstallation was successful, False otherwise
    """
    params = get_extension_uninstall_params()
    if not params:
        return False

    return uninstall_php_extension(params["domain"], params["extension_id"])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            success = cli_list_extensions()
        elif command == "install":
            success = cli_install_extension()
        elif command == "uninstall":
            success = cli_uninstall_extension()
        else:
            error(f"Unknown command: {command}")
            success = False
    else:
        # Default to list
        success = cli_list_extensions()
    
    sys.exit(0 if success else 1)
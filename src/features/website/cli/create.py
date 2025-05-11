"""
CLI interface for website creation.

This module provides a command-line interface for creating new websites,
handling user input validation and parameter collection.
"""

import re
import sys
from questionary import text, select, confirm
from typing import Optional, Dict, Any, Tuple

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import is_website_exists
from src.features.website.manager import create_website
from src.features.wordpress.cli.install import cli_install_wordpress
from src.common.utils.validation import is_valid_domain


@log_call
def get_website_creation_params() -> Optional[Dict[str, Any]]:
    """
    Prompt the user for website creation parameters.

    Returns:
        Optional[Dict[str, Any]]: Dictionary with domain and php_version if successful,
                                 None if cancelled
    """
    try:
        # Modified to continue asking until valid domain is entered
        valid_domain = False
        domain = None

        while not valid_domain:
            # Removed validate parameter to avoid automatically executing validation on each keystroke
            domain_input = text(
                "Enter domain name (e.g., example.com):"
            ).ask()

            # User cancelled input
            if not domain_input:
                warn("Website creation cancelled.")
                return None

            # Manually call validation function after user completes their input
            if is_valid_domain(domain_input):
                domain = domain_input
                valid_domain = True
            else:
                # Let them try again, validation error was already shown
                continue

        php_versions = ["8.2", "8.1", "8.0", "7.4"]
        php_version = select(
            "Select PHP version:",
            choices=php_versions,
            default="8.2"
        ).ask()

        confirm_create = confirm(
            f"Create website {domain} with PHP {php_version}?"
        ).ask()

        if not confirm_create:
            warn("Website creation cancelled.")
            return None

        return {
            "domain": domain,
            "php_version": php_version
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_create_website() -> bool:
    """
    CLI entry point for website creation.

    This function handles the interactive prompts for creating a new website
    and calls the creation function with the provided parameters.
    It also asks if the user wants to install WordPress after creation.

    Returns:
        bool: True if website creation was successful, False otherwise
    """
    params = get_website_creation_params()
    if not params:
        return False

    creation_success = create_website(params["domain"], params["php_version"])

    if creation_success:
        install_wp = confirm(
            f"Would you like to install WordPress on {params['domain']}?"
        ).ask()

        if install_wp:
            info(f"🔄 Proceeding with WordPress installation...")
            wp_install_success = cli_install_wordpress(domain=params['domain'])
            if not wp_install_success:
                warn(f"⚠️ WordPress installation failed, but website {params['domain']} was created successfully.")

    return creation_success


if __name__ == "__main__":
    success = cli_create_website()
    sys.exit(0 if success else 1)
"""
CLI interface for PHP version management.

This module provides a command-line interface for changing PHP versions
for websites.
"""

import sys
from questionary import select, confirm
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import select_website
from src.features.php.utils import php_choose_version, AVAILABLE_PHP_VERSIONS
from src.features.php.version import get_current_php_version, change_php_version


@log_call
def get_php_version_change_params() -> Optional[Dict[str, Any]]:
    """
    Prompt the user for PHP version change parameters.

    Returns:
        Optional[Dict[str, Any]]: Dictionary with domain and php_version if successful,
                                 None if cancelled
    """
    try:
        # Select website
        domain = select_website("Select website to change PHP version:")

        if not domain:
            warn("No website selected or no websites available.")
            return None

        # Get current PHP version
        current_version = get_current_php_version(domain)
        if current_version:
            info(f"Current PHP version: {current_version}")

        # Select new PHP version
        php_version = php_choose_version()

        if not php_version:
            return None

        # Skip if same version
        if current_version and php_version == current_version:
            warn(f"Selected version {php_version} is already in use. No change needed.")
            return None

        # Confirm version change
        confirm_change = confirm(
            f"Change PHP version for {domain} from {current_version} to {php_version}? "
            "This will restart the PHP container."
        ).ask()

        if not confirm_change:
            warn("PHP version change cancelled.")
            return None

        return {
            "domain": domain,
            "php_version": php_version
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_change_php_version() -> bool:
    """
    CLI entry point for changing PHP version.

    Returns:
        bool: True if version change was successful, False otherwise
    """
    params = get_php_version_change_params()
    if not params:
        return False

    return change_php_version(params["domain"], params["php_version"])


if __name__ == "__main__":
    success = cli_change_php_version()
    sys.exit(0 if success else 1)
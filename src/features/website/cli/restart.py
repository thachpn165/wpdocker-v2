"""
CLI interface for website restart.

This module provides a command-line interface for restarting websites,
handling user selection and confirmation.
"""

import sys
from questionary import confirm
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import select_website
from src.features.website.manager import restart_website


@log_call
def get_website_restart_params() -> Optional[Dict[str, Any]]:
    """
    Prompt the user for website restart parameters.

    Returns:
        Optional[Dict[str, Any]]: Dictionary with domain if successful,
                                 None if cancelled
    """
    try:
        domain = select_website("Select website to restart:")

        if not domain:
            warn("No website selected or no websites available.")
            return None

        confirm_restart = confirm(
            f"Restart website {domain}? This will temporarily interrupt service."
        ).ask()

        if not confirm_restart:
            warn("Website restart cancelled.")
            return None

        return {
            "domain": domain
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_restart_website() -> bool:
    """
    CLI entry point for website restart.

    This function handles the interactive prompts for restarting a website
    and calls the restart function with the provided parameters.

    Returns:
        bool: True if website restart was successful, False otherwise
    """
    params = get_website_restart_params()
    if not params:
        return False

    return restart_website(params["domain"])


if __name__ == "__main__":
    success = cli_restart_website()
    sys.exit(0 if success else 1)
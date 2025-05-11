"""
CLI interface for website deletion.

This module provides a command-line interface for deleting websites,
handling user confirmation and parameter validation.
"""

import sys
from questionary import confirm
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, warn, error, success
from src.features.website.utils import is_website_exists, select_website
from src.features.website.manager import delete_website


@log_call
def get_website_deletion_params() -> Optional[Dict[str, Any]]:
    """
    Prompt the user for website deletion parameters.

    Returns:
        Optional[Dict[str, Any]]: Dictionary with domain if successful,
                                 None if cancelled
    """
    try:
        domain = select_website("Select website to delete:")

        if not domain:
            warn("No website selected or no websites available.")
            return None

        confirm_delete = confirm(
            f"⚠️ Are you sure you want to delete website {domain}? "
            f"This will remove ALL files, database, and configurations."
        ).ask()

        if not confirm_delete:
            warn("Website deletion cancelled.")
            return None

        final_confirm = confirm(
            f"⚠️ FINAL WARNING: Delete website {domain}? This cannot be undone!"
        ).ask()

        if not final_confirm:
            warn("Website deletion cancelled.")
            return None

        return {
            "domain": domain
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_delete_website() -> bool:
    """
    CLI entry point for website deletion.

    This function handles the interactive prompts for deleting a website
    and calls the deletion function with the provided parameters.

    Returns:
        bool: True if website deletion was successful, False otherwise
    """
    params = get_website_deletion_params()
    if not params:
        return False

    return delete_website(params["domain"])


if __name__ == "__main__":
    success = cli_delete_website()
    sys.exit(0 if success else 1)
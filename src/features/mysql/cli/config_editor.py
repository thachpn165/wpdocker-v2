"""
CLI interface for MySQL configuration editing.

This module provides a command-line interface for editing MySQL server
configuration and managing configuration backups.
"""

import sys
from questionary import select, confirm
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, warn, error, success
from src.features.mysql.config import (
    edit_mysql_config,
    backup_mysql_config,
    restore_mysql_config
)


@log_call
def get_mysql_config_action() -> Optional[str]:
    """
    Prompt the user to select a MySQL configuration action.

    Returns:
        Optional[str]: Selected action or None if cancelled
    """
    try:
        action = select(
            "Select MySQL configuration action:",
            choices=[
                "Edit configuration",
                "Backup configuration",
                "Restore configuration from backup",
                "Cancel"
            ]
        ).ask()

        if not action or action == "Cancel":
            info("Operation cancelled.")
            return None

        return action
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def cli_mysql_config() -> bool:
    """
    CLI entry point for MySQL configuration management.

    Returns:
        bool: True if the operation was successful, False otherwise
    """
    action = get_mysql_config_action()
    if not action:
        return False

    if action == "Edit configuration":
        return edit_mysql_config()

    elif action == "Backup configuration":
        backup_path = backup_mysql_config()
        return bool(backup_path)

    elif action == "Restore configuration from backup":
        # Confirm restoration
        if not confirm("⚠️ Restore MySQL configuration from backup? This will overwrite current settings.").ask():
            info("Restoration cancelled.")
            return False

        return restore_mysql_config()

    return False


if __name__ == "__main__":
    success = cli_mysql_config()
    sys.exit(0 if success else 1)
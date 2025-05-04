"""
CLI interface for database restoration.

This module provides a command-line interface for restoring MySQL databases,
allowing users to select backup files and restore options.
"""

import os
import sys
from questionary import select, confirm
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, warn, error, success, debug
from src.common.utils.environment import env
from src.features.website.utils import select_website
from src.features.mysql.import_export import import_database


@log_call
def prompt_database_restore() -> Optional[Dict[str, Any]]:
    """
    Prompt the user for database restoration parameters.
    
    Returns:
        Optional[Dict[str, Any]]: Dictionary with domain, db_file, and reset parameters
                                 if successful, None if cancelled
    """
    try:
        # Select website for database restoration
        domain = select_website("🌐 Select website to restore database:")
        if not domain:
            info("Operation cancelled.")
            return None

        # Ask if the user wants to reset the database before restoration
        reset = confirm(
            "🗑️ Do you want to delete the current data before restoration?"
        ).ask()

        # Guide the user to prepare backup file
        sites_dir = env.get("SITES_DIR", "/opt/wp-docker/data/sites")
        backup_path = os.path.join(sites_dir, domain, "backups")
        
        info(f"📁 Please ensure the SQL file is placed in the directory: {backup_path}")

        # Check if backup directory exists, create if needed
        if not os.path.exists(backup_path):
            os.makedirs(backup_path, exist_ok=True)
            success(f"✅ Created backup directory at: {backup_path}")

        # Confirm file preparation
        if not confirm("❓ Have you placed the SQL file in the backup directory?").ask():
            info("Operation cancelled. Please prepare the backup file first.")
            return None

        # Get list of SQL files in the backup directory
        try:
            backup_files = [f for f in os.listdir(backup_path) if f.endswith('.sql')]
        except Exception as e:
            error(f"❌ Could not read backup directory: {e}")
            return None

        if not backup_files:
            error("❌ No SQL files found in the backup directory.")
            return None

        # Let user select a file to restore
        selected_file = select(
            "📦 Select SQL file to restore:",
            choices=backup_files
        ).ask()

        if not selected_file:
            info("Operation cancelled.")
            return None

        # Full path to the backup file
        db_file = os.path.join(backup_path, selected_file)

        # Confirm restoration
        if not confirm(f"⚠️ Confirm database restoration for {domain} from file {selected_file}?").ask():
            info("Database restoration cancelled.")
            return None

        return {
            "domain": domain,
            "db_file": db_file,
            "reset": reset,
            "file_name": selected_file
        }
    except (KeyboardInterrupt, EOFError):
        info("\nOperation cancelled.")
        return None


@log_call
def restore_database(domain: str, db_file: str, reset: bool = True) -> bool:
    """
    Restore a database from an SQL file.
    
    Args:
        domain: Website domain name
        db_file: Path to the SQL backup file
        reset: Whether to reset the database before restoration
        
    Returns:
        bool: True if restoration was successful, False otherwise
    """
    try:
        import_database(domain, db_file, reset)
        return True
    except Exception as e:
        error(f"❌ Error restoring database: {e}")
        return False


@log_call
def cli_restore_database() -> bool:
    """
    CLI entry point for database restoration.
    
    Returns:
        bool: True if restoration was successful, False otherwise
    """
    params = prompt_database_restore()
    if not params:
        return False
    
    domain = params["domain"]
    db_file = params["db_file"]
    reset = params["reset"]
    file_name = params["file_name"]
    
    success_status = restore_database(domain, db_file, reset)
    
    if success_status:
        reset_text = "deleted old data" if reset else "kept old data"
        success(f"✅ Database restoration completed for website {domain}.")
        info(f"📊 Restoration details:")
        info(f"  • SQL file: {file_name}")
        info(f"  • Old data: {reset_text}")
    else:
        error(f"❌ Database restoration for website {domain} failed.")
    
    return success_status


if __name__ == "__main__":
    success = cli_restore_database()
    sys.exit(0 if success else 1)
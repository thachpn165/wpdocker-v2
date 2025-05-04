"""
MySQL import and export functions.

This module provides functions for importing and exporting MySQL databases,
useful for backup and restore operations.
"""

import os
from datetime import datetime
from typing import Optional

from src.common.logging import log_call, info, error
from src.common.utils.environment import env_required, env
from src.common.containers.container import Container
from src.features.mysql.mysql_exec import run_mysql_dump, run_mysql_import, run_mysql_command
from src.features.website.utils import get_site_config


# Ensure required environment variables are set
env_required(["MYSQL_CONTAINER_NAME"])
mysql_container = Container(env["MYSQL_CONTAINER_NAME"])


@log_call
def export_database(domain: str, target_folder: str) -> Optional[str]:
    """
    Export database for a website to a SQL file.
    
    Args:
        domain: Website domain name
        target_folder: Folder where to save the SQL file
        
    Returns:
        Path to the exported SQL file or None if export failed
    """
    site_config = get_site_config(domain)
    if not site_config or not hasattr(site_config, 'mysql') or not site_config.mysql:
        error(f"❌ MySQL configuration not found for website: {domain}")
        return None

    os.makedirs(target_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"db_{domain}_{timestamp}.sql"
    filepath = os.path.join(target_folder, filename)

    run_mysql_dump(site_config.mysql.db_name, "/tmp/export.sql")
    mysql_container.copy_from("/tmp/export.sql", filepath)
    info(f"✅ Database exported for {domain} to: {filepath}")
    
    return filepath


@log_call
def import_database(domain: str, db_file: str, reset: bool = True) -> bool:
    """
    Import database for a website from a SQL file.
    
    Args:
        domain: Website domain name
        db_file: Path to the SQL file
        reset: Whether to reset the database before importing
        
    Returns:
        True if import succeeded, False otherwise
    """
    site_config = get_site_config(domain)
    if not site_config or not hasattr(site_config, 'mysql') or not site_config.mysql:
        error(f"❌ MySQL configuration not found for website: {domain}")
        return False

    db_name = site_config.mysql.db_name

    if reset:
        run_mysql_command(f"DROP DATABASE IF EXISTS {db_name}; CREATE DATABASE {db_name};")
        info(f"🗑️ Database {db_name} reset before import.")

    mysql_container.copy_to(db_file, "/tmp/import.sql")
    run_mysql_import("/tmp/import.sql", db_name)
    info(f"✅ Data imported from {db_file} to database {db_name} for website {domain}.")
    
    return True
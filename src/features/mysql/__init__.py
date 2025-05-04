"""
MySQL database management functionality.

This package provides functionality for MySQL database operations,
including creating, importing, exporting, and managing databases.
"""

# Core database operations
from src.features.mysql.database import (
    create_database,
    create_database_user,
    grant_privileges,
    setup_database_for_website,
    delete_database,
    delete_database_user
)

# Import/export functionality
from src.features.mysql.import_export import export_database, import_database

# Command execution
from src.features.mysql.mysql_exec import run_mysql_command, run_mysql_import, run_mysql_dump

# Configuration management
from src.features.mysql.config import edit_mysql_config, backup_mysql_config, restore_mysql_config

# Utilities
from src.features.mysql.utils import get_mysql_root_password, get_domain_db_pass, detect_mysql_client

# CLI interfaces
from src.features.mysql.cli import cli_restore_database, cli_mysql_config

__all__ = [
    # Core database operations
    'create_database',
    'create_database_user',
    'grant_privileges',
    'setup_database_for_website',
    'delete_database',
    'delete_database_user',
    
    # Import/export functionality
    'export_database',
    'import_database',
    
    # Command execution
    'run_mysql_command',
    'run_mysql_import',
    'run_mysql_dump',
    
    # Configuration management
    'edit_mysql_config',
    'backup_mysql_config',
    'restore_mysql_config',
    
    # Utilities
    'get_mysql_root_password',
    'get_domain_db_pass',
    'detect_mysql_client',
    
    # CLI interfaces
    'cli_restore_database',
    'cli_mysql_config'
]
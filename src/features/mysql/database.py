"""
MySQL database management functions.

This module provides functions for creating, deleting, and managing MySQL databases
and database users for websites.
"""

import random
import string
from typing import Dict, Tuple, Optional, Any

from src.common.logging import log_call, info, warn, error, debug, success
from src.common.utils.environment import env
from src.common.containers.container import Container

from src.features.mysql.utils import get_mysql_root_password
from src.features.mysql.mysql_exec import run_mysql_command


@log_call
def create_database(domain: str) -> Optional[str]:
    """
    Create a new database for a website.
    
    Args:
        domain: Website domain name
        
    Returns:
        Database name if created successfully, None otherwise
    """
    db_name = f"{domain.replace('.', '_')}_wpdb"
    
    try:
        run_mysql_command(
            f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
        info(f"✅ Created database: {db_name}")
        return db_name
    except Exception as e:
        error(f"❌ Error creating database: {e}")
        return None


@log_call
def create_database_user(domain: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Create a new database user for a website.
    
    Args:
        domain: Website domain name
        
    Returns:
        Tuple of (username, password) if created successfully, (None, None) otherwise
    """
    db_user = f"{domain.replace('.', '_')}_wpuser"
    db_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    try:
        run_mysql_command(
            f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_pass}';"
        )
        info(f"✅ Created user: {db_user}")
        return db_user, db_pass
    except Exception as e:
        error(f"❌ Error creating database user: {e}")
        return None, None


@log_call
def grant_privileges(db_name: str, db_user: str) -> bool:
    """
    Grant all privileges on a database to a user.
    
    Args:
        db_name: Database name
        db_user: Username
        
    Returns:
        True if privileges were granted successfully, False otherwise
    """
    try:
        run_mysql_command(
            f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'%'; FLUSH PRIVILEGES;"
        )
        info(f"✅ Granted privileges to user {db_user} on database {db_name}")
        return True
    except Exception as e:
        error(f"❌ Error granting database privileges: {e}")
        return False


@log_call
def setup_database_for_website(domain: str) -> Optional[Dict[str, str]]:
    """
    Set up a complete database environment for a website.
    
    This includes creating a database, creating a user, and granting privileges.
    
    Args:
        domain: Website domain name
        
    Returns:
        Dict with db_name, db_user, and db_pass if setup was successful, None otherwise
    """
    db_name = create_database(domain)
    if not db_name:
        return None
        
    db_user, db_pass = create_database_user(domain)
    if not db_user or not db_pass:
        return None
        
    if not grant_privileges(db_name, db_user):
        return None

    return {
        "db_name": db_name,
        "db_user": db_user,
        "db_pass": db_pass
    }


@log_call
def delete_database(domain: str) -> bool:
    """
    Delete a database for a website.
    
    Args:
        domain: Website domain name
        
    Returns:
        True if database was deleted successfully, False otherwise
    """
    db_name = f"{domain.replace('.', '_')}_wpdb"
    
    try:
        # Escape backticks in the SQL command properly
        run_mysql_command(f"DROP DATABASE IF EXISTS {db_name};")
        info(f"🗑️ Deleted database: {db_name}")
        return True
    except Exception as e:
        error(f"❌ Error deleting database {db_name}: {e}")
        return False


@log_call
def delete_database_user(domain: str) -> bool:
    """
    Delete a database user for a website.
    
    Args:
        domain: Website domain name
        
    Returns:
        True if user was deleted successfully, False otherwise
    """
    db_user = f"{domain.replace('.', '_')}_wpuser"
    
    try:
        run_mysql_command(f"DROP USER IF EXISTS '{db_user}'@'%'; FLUSH PRIVILEGES;")
        info(f"🗑️ Deleted user: {db_user}")
        return True
    except Exception as e:
        error(f"❌ Error deleting user {db_user}: {e}")
        return False
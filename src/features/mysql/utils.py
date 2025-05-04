"""
MySQL utility functions.

This module provides utility functions for MySQL database operations,
including password retrieval and client detection.
"""

from src.common.config.manager import ConfigManager
from src.common.logging import debug, error
from src.common.utils.crypto import decrypt
from src.common.containers.container import Container


def get_mysql_root_password() -> str:
    """
    Get decrypted MySQL root password from config.json.
    
    Returns:
        Decrypted root password or None if not found
    """
    config = ConfigManager()
    encrypted_pass = config.get().get("mysql", {}).get("root_passwd")
    if not encrypted_pass:
        error("❌ mysql.root_passwd not found in config.")
        return None
    try:
        password = decrypt(encrypted_pass)
        debug(f"🔑 MySQL root password (decrypted): {password}")
        return password
    except Exception as e:
        error(f"❌ Error decrypting MySQL password: {e}")
        return None


def get_domain_db_pass(domain: str) -> str:
    """
    Get decrypted database password for a specific domain from config.json.
    
    Args:
        domain: Website domain name
        
    Returns:
        Decrypted database password or None if not found
    """
    # Import here to avoid circular imports
    from src.features.website.utils import get_site_config
    
    site_config = get_site_config(domain)
    if not site_config or not hasattr(site_config, 'mysql') or not site_config.mysql:
        error(f"❌ MySQL configuration for domain {domain} not found in config.")
        return None

    encrypted_pass = site_config.mysql.db_pass if site_config.mysql else None
    if not encrypted_pass:
        error(f"❌ db_pass for domain {domain} not found in configuration.")
        return None

    try:
        password = decrypt(encrypted_pass)
        return password
    except Exception as e:
        error(f"Error decrypting database password for domain {domain}: {e}")
        return None


def detect_mysql_client(container: Container) -> str:
    """
    Detect which MySQL client is available in the container.
    
    Args:
        container: Container instance
        
    Returns:
        Client command name ('mariadb' or 'mysql')
        
    Raises:
        RuntimeError: If no MySQL client is found
    """
    result = container.exec(["which", "mariadb"])
    if result is not None and result.strip() != "":
        return "mariadb"

    result = container.exec(["which", "mysql"])
    if result is not None and result.strip() != "":
        return "mysql"

    raise RuntimeError("❌ Neither mariadb nor mysql command found in container.")
"""
MySQL utility functions.

This module provides utility functions for MySQL database operations,
including password retrieval and client detection.
"""

from src.common.config.manager import ConfigManager
from src.common.logging import debug, error, warn
from src.common.utils.crypto import decrypt
from src.common.containers.container import Container


def get_mysql_root_password() -> str:
    """
    Get MySQL root password by decrypting it from config.json.
    
    The password is stored encrypted in config.json during the bootstrap process
    and should be the authoritative source. Only if decryption fails, we'll try
    to read from docker-compose as a fallback.
    
    Returns:
        Decrypted MySQL root password or None if not found
    """
    # Primary source: Try to decrypt from config.json first
    config = ConfigManager()
    encrypted_pass = config.get().get("mysql", {}).get("root_passwd")
    if not encrypted_pass:
        error("❌ mysql.root_passwd not found in config.")
        return _fallback_get_password_from_compose()
    
    try:
        password = decrypt(encrypted_pass)
        debug(f"🔑 Successfully decrypted MySQL root password from config.json")
        return password
    except Exception as e:
        error(f"❌ Error decrypting MySQL password: {e}")
        debug("Falling back to docker-compose.mysql.yml as password source")
        return _fallback_get_password_from_compose()


def _fallback_get_password_from_compose() -> str:
    """
    Fallback method to extract MySQL root password from docker-compose file.
    This should only be used if the primary method (decrypting from config.json) fails.
    
    Returns:
        MySQL root password or None if not found
    """
    import os
    from src.common.utils.environment import env
    
    # Try to read from docker-compose file as fallback
    compose_path = os.path.join(env.get("INSTALL_DIR", "/opt/wp-docker"), "docker-compose", "docker-compose.mysql.yml")
    if os.path.exists(compose_path):
        try:
            debug(f"Attempting to read MySQL password from compose file: {compose_path}")
            with open(compose_path, 'r') as file:
                content = file.read()
                
            # Extract password from docker-compose file
            import re
            password_match = re.search(r'MYSQL_ROOT_PASSWORD:\s*([^\s]+)', content)
            if password_match:
                password = password_match.group(1).strip()
                debug(f"🔑 Using MySQL root password from docker-compose file as fallback")
                warn("⚠️ Using password from docker-compose file may be less reliable")
                return password
        except Exception as e:
            debug(f"Failed to extract password from docker-compose file: {e}")
    
    error("❌ Could not retrieve MySQL root password from any source")
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
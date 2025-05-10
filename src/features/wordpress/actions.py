"""
WordPress installation actions.

This module provides functions for various WordPress installation steps, 
including downloading, configuring, and installing the WordPress core.
"""

import os
from typing import Dict, Any, Optional, List, Tuple

from src.common.logging import debug, info, warn, error, success, log_call
from src.common.utils.environment import env
from src.common.containers.container import Container

from src.features.website.utils import ensure_www_data_ownership, get_site_config, set_site_config, delete_site_config
from src.features.mysql.utils import get_domain_db_pass, detect_mysql_client
from src.features.php.client import init_php_client
from src.features.wordpress.manager import WordPressAutoUpdateManager

# Configuration keys to save in config.json after WordPress installation
CONFIG_KEYS_AFTER_INSTALL = {
    "cache": "no-cache",

}


@log_call
def check_containers(domain: str) -> bool:
    """
    Check if all required containers for WordPress installation are running.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if all containers are running, False otherwise
    """
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    if not wpcli.running():
        error(f"❌ WP-CLI container ({wpcli.name}) is not running.")
        return False

    php = init_php_client(domain)
    if not php.running():
        error(f"❌ PHP container {php.name} is not running.")
        return False

    mysql = Container(env["MYSQL_CONTAINER_NAME"])
    if not mysql.running():
        error(f"❌ MySQL container {mysql.name} is not running.")
        return False

    return True


@log_call
def download_core(domain: str) -> bool:
    """
    Download WordPress core files to the website directory.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    sites_dir = env["SITES_DIR"]
    wordpress_path = os.path.join(sites_dir, domain, "wordpress")

    # Check if the directory on the host is empty
    is_empty = not os.path.exists(wordpress_path) or not os.listdir(wordpress_path)

    if is_empty:
        debug(f"📥 Downloading WordPress to {wordpress_path}...")
        wpcli.exec(["wp", "core", "download"], workdir=f"/var/www/html/{domain}/wordpress")
    else:
        warn(f"📂 WordPress is already installed at {wordpress_path}. Skipping download.")

    return True


@log_call
def delete_core(domain: str) -> None:
    """
    Delete WordPress core files from the website directory.
    
    Args:
        domain: Website domain name
    """
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"
    wpcli.exec(["rm", "-rf", wordpress_path])
    warn(f"🧹 Removed WordPress files at {wordpress_path}.")


@log_call
def generate_config(domain: str) -> bool:
    """
    Generate wp-config.php file from sample configuration.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if configuration was generated successfully, False otherwise
    """
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"
    wpcli.exec(["cp", "wp-config-sample.php", "wp-config.php"], workdir=wordpress_path)
    return True


@log_call
def delete_config(domain: str) -> None:
    """
    Delete wp-config.php file.
    
    Args:
        domain: Website domain name
    """
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress/wp-config.php"
    wpcli.exec(["rm", "-f", wordpress_path])
    warn(f"🗑️ Removed wp-config.php at {wordpress_path}.")


@log_call
def configure_db(domain: str) -> bool:
    """
    Configure WordPress database settings in wp-config.php.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if database configuration was successful, False otherwise
    """
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"
    site_config = get_site_config(domain)
    db_info = site_config.mysql if site_config and hasattr(site_config, 'mysql') else None
    
    if not db_info:
        error("❌ Missing database information in configuration.")
        return False
        
    db_name = getattr(db_info, "db_name", None)
    db_user = getattr(db_info, "db_user", None)
    db_pass = get_domain_db_pass(domain)
    db_host = env["MYSQL_CONTAINER_NAME"]

    if not all([db_name, db_user, db_pass]):
        error("❌ Missing database credentials in configuration.")
        return False

    replacements = {
        "database_name_here": db_name,
        "username_here": db_user,
        "password_here": db_pass,
        "localhost": db_host,
    }
    
    for search, replace in replacements.items():
        wpcli.exec(["sed", "-i", f"s/{search}/{replace}/g", "wp-config.php"], workdir=wordpress_path)

    return True


@log_call
def check_database(domain: str) -> bool:
    """
    Verify database connection with WordPress credentials.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if database connection is successful, False otherwise
    """
    site_config = get_site_config(domain)
    db_info = site_config.mysql if site_config and hasattr(site_config, 'mysql') else None
    
    if not db_info:
        error("❌ Missing database information in configuration.")
        return False
        
    db_name = getattr(db_info, "db_name", None)
    db_user = getattr(db_info, "db_user", None)
    db_pass = get_domain_db_pass(domain)

    if not all([db_name, db_user, db_pass]):
        error("❌ Missing database credentials in configuration.")
        return False

    mysql = Container(env["MYSQL_CONTAINER_NAME"])
    client_cmd = detect_mysql_client(mysql)
    check_cmd = [client_cmd, "-u", db_user, f"-p{db_pass}", "-e", f"USE {db_name};"]
    
    if mysql.exec(check_cmd) is None:
        error("❌ Database connection failed.")
        return False
        
    return True


@log_call
def core_install(domain: str, site_url: str, title: str, admin_user: str, 
                admin_pass: str, admin_email: str) -> bool:
    """
    Install WordPress core with given settings.
    
    Args:
        domain: Website domain name
        site_url: Website URL
        title: Website title
        admin_user: Admin username
        admin_pass: Admin password
        admin_email: Admin email
        
    Returns:
        bool: True if installation was successful, False otherwise
    """
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"
    
    try:
        wpcli.exec([
            "wp", "core", "install",
            f"--url={site_url}",
            f"--title={title}",
            f"--admin_user={admin_user}",
            f"--admin_password={admin_pass}",
            f"--admin_email={admin_email}",
            "--skip-email",
        ], workdir=wordpress_path)
        return True
    except Exception as e:
        error(f"❌ WordPress core installation failed: {e}")
        return False


@log_call
def uninstall(domain: str) -> None:
    """
    Remove WordPress installation completely.
    
    Args:
        domain: Website domain name
    """
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"
    
    try:
        wpcli.exec(["wp", "db", "drop", "--yes"], workdir=wordpress_path)
    except Exception:
        pass  # Ignore if database drop fails
        
    wpcli.exec(["rm", "-rf", wordpress_path])
    warn(f"🧨 Removed WordPress installation at {wordpress_path}.")


@log_call
def fix_permissions(domain: str) -> bool:
    """
    Fix file permissions for WordPress installation.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if permissions were fixed successfully, False otherwise
    """
    php = init_php_client(domain)
    ensure_www_data_ownership(php.name, "/var/www/html/")
    return True


@log_call
def verify_installation(domain: str) -> bool:
    """
    Verify WordPress installation is complete and functioning.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if installation is verified, False otherwise
    """
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"
    result = wpcli.exec(["wp", "core", "is-installed"], workdir=wordpress_path)
    return result is not None


@log_call
def save_post_install_config(domain: str) -> bool:
    """
    Save configuration after WordPress installation.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if configuration was saved successfully, False otherwise
    """
    site_config = get_site_config(domain)
    if not site_config:
        error(f"❌ Site configuration for {domain} not found for updating.")
        return False

    for subkey, value in CONFIG_KEYS_AFTER_INSTALL.items():
        setattr(site_config, subkey, value)
        debug(f"📝 Set site_config.{subkey} = {value}")

    set_site_config(domain, site_config)
    return True


@log_call
def delete_post_install_config(domain: str) -> bool:
    """
    Delete post-installation configuration keys.
    
    Args:
        domain: Website domain name
        
    Returns:
        bool: True if configuration was deleted successfully, False otherwise
    """
    for subkey in CONFIG_KEYS_AFTER_INSTALL.keys():
        deleted = delete_site_config(domain, subkey=subkey)
        if deleted:
            debug(f"🗑️ Deleted config site.{domain}.{subkey}")
        else:
            warn(f"⚠️ Config site.{domain}.{subkey} not found for deletion")
    return True


def toggle_theme_auto_update_action(domain: str) -> bool:
    return WordPressAutoUpdateManager().toggle_theme_auto_update(domain)

def toggle_plugin_auto_update_action(domain: str) -> bool:
    return WordPressAutoUpdateManager().toggle_plugin_auto_update(domain)
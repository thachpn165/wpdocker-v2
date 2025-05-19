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
    is_empty = not os.path.exists(
        wordpress_path) or not os.listdir(wordpress_path)

    if is_empty:
        debug(f"📥 Downloading WordPress to {wordpress_path}...")
        
        # First try to ensure the directory exists with proper permissions
        wpcli.exec(["mkdir", "-p", f"/var/www/html/{domain}/wordpress"],
                  user="www-data")
        
        # Run the core download command with www-data user
        result = wpcli.exec(["wp", "core", "download"],
                   workdir=f"/var/www/html/{domain}/wordpress",
                   user="www-data")
        
        if result is None:
            error(f"❌ Failed to download WordPress for {domain}")
            return False
    else:
        warn(
            f"📂 WordPress is already installed at {wordpress_path}. Skipping download.")

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
    result = wpcli.exec(["cp", "wp-config-sample.php", "wp-config.php"],
               workdir=wordpress_path,
               user="www-data")
    if result is None:
        error(f"❌ Failed to create wp-config.php for {domain}")
        return False
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
    db_info = site_config.mysql if site_config and hasattr(
        site_config, 'mysql') else None

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
        result = wpcli.exec(["sed", "-i", f"s/{search}/{replace}/g",
                   "wp-config.php"], workdir=wordpress_path, user="www-data")
        if result is None:
            error(f"❌ Failed to configure database in wp-config.php for {domain}")
            return False

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
    db_info = site_config.mysql if site_config and hasattr(
        site_config, 'mysql') else None

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
    check_cmd = [client_cmd, "-u", db_user,
                 f"-p{db_pass}", "-e", f"USE {db_name};"]

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
        result = wpcli.exec([
            "wp", "core", "install",
            f"--url={site_url}",
            f"--title={title}",
            f"--admin_user={admin_user}",
            f"--admin_password={admin_pass}",
            f"--admin_email={admin_email}",
            "--skip-email",
        ], workdir=wordpress_path, user="www-data")
        
        if result is None:
            error(f"❌ WordPress core installation failed for {domain}")
            return False
            
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
    result = wpcli.exec(["wp", "core", "is-installed"], 
                       workdir=wordpress_path, 
                       user="www-data")
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


@log_call
def toggle_wp_login_protection(domain: str) -> tuple:
    """
    Bật/tắt tính năng bảo vệ wp-login.php cho một website.

    Args:
        domain: Tên miền website

    Returns:
        Tuple chứa (thành công, trạng thái mới, thông tin đăng nhập nếu có)
    """
    from src.features.website.utils import get_site_config, set_site_config
    from src.features.wordpress.utils import create_or_update_htpasswd, init_config_wplogin_protection
    from src.features.wordpress.utils import delete_htpasswd, delete_wplogin_protection
    from src.features.wordpress.utils import add_protect_include_to_vhost, remove_protect_include_from_vhost
    from src.features.webserver import WebserverReload

    # Lấy cấu hình hiện tại
    site_config = get_site_config(domain)
    if not site_config:
        error(f"❌ Không tìm thấy cấu hình cho website {domain}")
        return False, False, None

    # Kiểm tra và tạo WordPress config nếu cần
    if not site_config.wordpress:
        from src.features.website.models.site_config import WordPressConfig
        site_config.wordpress = WordPressConfig()

    # Lấy trạng thái bảo vệ hiện tại
    current_status = site_config.wordpress.wp_login_protected
    new_status = not current_status

    # Cập nhật trạng thái trong cấu hình
    site_config.wordpress.wp_login_protected = new_status
    set_site_config(domain, site_config)

    login_info = None

    if new_status:
        # Bật bảo vệ - tạo htpasswd và cấu hình webserver
        login_info = create_or_update_htpasswd(domain)
        if init_config_wplogin_protection(domain):
            # Thêm include vào vhost
            if not add_protect_include_to_vhost(domain):
                error(
                    f"❌ Không thể thêm include bảo vệ wp-login.php vào vhost cho {domain}")
                return False, new_status, login_info
            success(f"✅ Đã bật bảo vệ wp-login.php cho {domain}")
        else:
            error(f"❌ Không thể tạo cấu hình bảo vệ wp-login.php cho {domain}")
            return False, new_status, login_info
    else:
        # Tắt bảo vệ - xóa htpasswd và cấu hình webserver
        delete_htpasswd(domain)
        if delete_wplogin_protection(domain):
            # Xóa include khỏi vhost
            if not remove_protect_include_from_vhost(domain):
                error(
                    f"❌ Không thể xóa include bảo vệ wp-login.php khỏi vhost cho {domain}")
                return False, new_status, None
            success(f"✅ Đã tắt bảo vệ wp-login.php cho {domain}")
        else:
            error(f"❌ Không thể xóa cấu hình bảo vệ wp-login.php cho {domain}")
            return False, new_status, None

    # Reload webserver để áp dụng thay đổi
    info("🔄 Đang reload webserver để áp dụng thay đổi...")
    WebserverReload.webserver_reload()

    return True, new_status, login_info

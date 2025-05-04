"""
Website actions for creating, configuring and deleting websites.

This module provides functions that handle the steps involved in setting up
a new website instance, including directory structure, container configuration,
database setup, and NGINX configuration.
"""

import os
import inspect
import shutil
from typing import List, Tuple, Dict, Any, Optional, Callable

from src.common.logging import log_call, info, warn, error, success, debug
from src.common.utils.environment import env
from src.core.containers.compose import Compose
from src.common.containers.container import Container
from src.common.config.manager import ConfigManager

from src.features.website.utils import (
    is_website_exists, 
    get_site_config, 
    set_site_config, 
    delete_site_config,
    calculate_php_fpm_values
)
from src.features.website.models.site_config import (
    SiteConfig, 
    SiteLogs, 
    SiteMySQL, 
    SitePHP
)

from src.features.mysql.database import (
    setup_database_for_website, 
    delete_database, 
    delete_database_user
)
from src.features.nginx.manager import restart as nginx_restart
from src.features.ssl.installer import install_selfsigned_ssl
from src.features.php.client import init_php_client
from src.common.utils.crypto import encrypt


@log_call
def setup_directories(domain: str) -> None:
    """
    Create the basic directory structure for a website.
    
    Args:
        domain: Website domain name
    """
    sites_dir = env["SITES_DIR"]
    site_dir = os.path.join(sites_dir, domain)

    os.makedirs(os.path.join(site_dir, "php"), exist_ok=True)
    os.makedirs(os.path.join(site_dir, "wordpress"), exist_ok=True)
    os.makedirs(os.path.join(site_dir, "logs"), exist_ok=True)
    os.makedirs(os.path.join(site_dir, "backups"), exist_ok=True)
    os.makedirs(os.path.join(site_dir, "ssl"), exist_ok=True)

    for log_file in ["access.log", "error.log", "php_error.log", "php_slow.log"]:
        log_path = os.path.join(site_dir, "logs", log_file)
        open(log_path, "a").close()
        os.chmod(log_path, 0o666)


def cleanup_directories(domain: str) -> None:
    """
    Remove the entire website directory structure.
    
    Args:
        domain: Website domain name
    """
    sites_dir = env["SITES_DIR"]
    site_dir = os.path.join(sites_dir, domain)
    if os.path.isdir(site_dir):
        shutil.rmtree(site_dir)
        info(f"🗑️ Removed directory {site_dir}")


@log_call
def setup_config(domain: str, php_version: str) -> None:
    """
    Set up the website configuration in the global config store.
    
    Args:
        domain: Website domain name
        php_version: PHP version to use for the website
    """
    sites_dir = env["SITES_DIR"]
    logs_dir = os.path.join(sites_dir, domain, "logs")

    php_container_name = f"{domain}-php"
    container = init_php_client(domain)

    site_logs = SiteLogs(
        access=os.path.join(logs_dir, "access.log"),
        error=os.path.join(logs_dir, "error.log"),
        php_error=os.path.join(logs_dir, "php_error.log"),
        php_slow=os.path.join(logs_dir, "php_slow.log")
    )

    site_config = get_site_config(domain) or SiteConfig(
        domain=domain,
        php=SitePHP(
            php_version=php_version,
            php_container=container.name,
            php_installed_extensions=[]
        ),
        logs=site_logs,
        cache="no-cache",
    )

    db_info = setup_database_for_website(domain)
    if not db_info:
        error("❌ Could not create database for website.")
        return

    site_config.mysql = SiteMySQL(
        db_name=db_info["db_name"],
        db_user=db_info["db_user"],
        db_pass=encrypt(db_info["db_pass"])
    )

    # Update logs, container_id, php_version if changed
    site_config.logs = site_logs
    site_config.php = SitePHP(
        php_version=php_version,
        php_container=container.name,
        php_installed_extensions=[]
    )

    set_site_config(domain, site_config)
    info(f"✅ Saved website {domain} information to configuration")


def cleanup_config(domain: str) -> None:
    """
    Remove the website configuration from the global config store.
    
    Args:
        domain: Website domain name
    """
    delete_site_config(domain, subkey=None)
    info(f"🗑️ Removed website {domain} configuration")


def setup_php_configs(domain: str, php_version: str) -> None:
    """
    Create php.ini and php-fpm.conf files for the website.
    
    Args:
        domain: Website domain name
        php_version: PHP version to use for the website
    """
    sites_dir = env["SITES_DIR"]
    site_dir = os.path.join(sites_dir, domain)
    install_dir = env["INSTALL_DIR"]
    php_ini_template = os.path.join(
        install_dir, "core", "templates", "php.ini.template")
    
    config_manager = ConfigManager()
    timezone = config_manager.get().get("core", {}).get("timezone", "UTC")

    php_ini_target = os.path.join(site_dir, "php", "php.ini")
    if os.path.isfile(php_ini_template):
        with open(php_ini_template, "r") as f:
            content = f.read().replace("${TIMEZONE}", timezone)
        with open(php_ini_target, "w") as f:
            f.write(content)

    fpm_values = calculate_php_fpm_values()
    php_fpm_conf_path = os.path.join(site_dir, "php", "php-fpm.conf")
    with open(php_fpm_conf_path, "w") as f:
        f.write(f"""[www]
user = www-data
group = www-data
listen = 9000
pm = {fpm_values['pm_mode']}
pm.max_children = {fpm_values['max_children']}
pm.start_servers = {fpm_values['start_servers']}
pm.min_spare_servers = {fpm_values['min_spare_servers']}
pm.max_spare_servers = {fpm_values['max_spare_servers']}
pm.process_idle_timeout = 10s
pm.max_requests = 1000
slowlog=/var/www/logs/php_slow.log
request_slowlog_timeout = 10
request_terminate_timeout = 60
""")


@log_call
def setup_compose_php(domain: str, php_version: str) -> Dict[str, str]:
    """
    Create and start the PHP docker container for the website.
    
    Args:
        domain: Website domain name
        php_version: PHP version to use for the website
        
    Returns:
        Dict containing container information
    """
    install_dir = env["INSTALL_DIR"]
    sites_dir = env["SITES_DIR"]
    site_dir = os.path.join(sites_dir, domain)

    docker_compose_template = os.path.join(
        install_dir, "core", "templates", "docker-compose.php.yml.template")
    docker_compose_target = os.path.join(site_dir, "docker-compose.php.yml")
    php_container = f"{domain}-php"

    compose = Compose(
        template_path=docker_compose_template,
        output_path=docker_compose_target,
        env_map={
            "PROJECT_NAME": env["PROJECT_NAME"],
            "CORE_DIR": os.path.join(install_dir, "core"),
            "DOCKER_NETWORK": env["DOCKER_NETWORK"],
            "domain": domain,
            "php_container": php_container,
            "php_version": php_version
        },
        name=php_container
    )
    compose.ensure_ready()

    # Ensure www-data ownership for /var/www/html in the PHP container
    container = Container(name=php_container)
    container.exec(["chown", "-R", "www-data:www-data", f"/var/www/html"], user="root")
    debug(f"✅ Set www-data ownership for /var/www/html in container {php_container}")

    return {
        "container_id": php_container,
        "container_name": php_container,
        "domain": domain,
    }


@log_call(log_vars=["domain"])
def cleanup_compose_php(domain: str) -> None:
    """
    Remove the PHP docker container and compose file for the website.
    
    Args:
        domain: Website domain name
    """
    site_config = get_site_config(domain)
    container_id = site_config.php.php_container if site_config and site_config.php else None
    if container_id:
        container = Container(name=container_id)
        if container.exists():
            debug(f"Stopping and removing container {container_id}...")
            container.stop()
            container.remove()

    docker_compose_target = os.path.join(
        env["SITES_DIR"], domain, "docker-compose.php.yml")
    if os.path.isfile(docker_compose_target):
        os.remove(docker_compose_target)
        info(f"🗑️ Removed PHP docker-compose file for {domain}")


@log_call
def setup_nginx_vhost(domain: str) -> None:
    """
    Create NGINX virtual host configuration for the website.
    
    Args:
        domain: Website domain name
    """
    install_dir = env["INSTALL_DIR"]
    nginx_template = os.path.join(
        install_dir, "core", "templates", "nginx-vhost.conf.template")
    nginx_target_dir = os.path.join(env["CONFIG_DIR"], "nginx", "conf.d")
    nginx_target_path = os.path.join(nginx_target_dir, f"{domain}.conf")

    if not os.path.exists(nginx_target_dir):
        os.makedirs(nginx_target_dir, exist_ok=True)

    if os.path.isfile(nginx_template):
        with open(nginx_template, "r") as f:
            content = f.read().replace("${DOMAIN}", domain)
        with open(nginx_target_path, "w") as f:
            f.write(content)
        nginx_restart()


def cleanup_nginx_vhost(domain: str) -> None:
    """
    Remove NGINX virtual host configuration for the website.
    
    Args:
        domain: Website domain name
    """
    nginx_target_path = os.path.join(
        env["CONFIG_DIR"], "nginx", "conf.d", f"{domain}.conf")
    if os.path.isfile(nginx_target_path):
        os.remove(nginx_target_path)
        info(f"🗑️ Removed NGINX vhost file for {domain}")


def cleanup_database(domain: str) -> None:
    """
    Remove database and database user for the website.
    
    Args:
        domain: Website domain name
    """
    delete_database(domain)
    delete_database_user(domain)


@log_call
def setup_ssl(domain: str, php_version: str = None) -> None:
    """
    Set up SSL for a website by installing a self-signed certificate.
    
    Args:
        domain: The domain name
        php_version: Not used for SSL setup, included for action signature compatibility
    """
    success = install_selfsigned_ssl(domain)
    if success:
        info(f"✅ Self-signed SSL certificate installed for {domain}")
    else:
        warn(f"⚠️ Failed to install self-signed SSL certificate for {domain}")


# Setup and cleanup action pairs for website creation
WEBSITE_SETUP_ACTIONS = [
    (setup_directories, cleanup_directories),
    (setup_php_configs, None),
    (setup_compose_php, cleanup_compose_php),
    (setup_ssl, None),
    (setup_nginx_vhost, cleanup_nginx_vhost),
    (setup_config, cleanup_config),  # Keep this last
]

# Actions for website cleanup/deletion
WEBSITE_CLEANUP_ACTIONS = [
    cleanup_nginx_vhost,
    cleanup_compose_php,
    cleanup_database,
    cleanup_config,
    cleanup_directories
]
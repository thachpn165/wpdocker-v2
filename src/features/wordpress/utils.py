"""
WordPress utility functions.

This module provides utility functions for WordPress operations,
including WP-CLI command execution.
"""

from typing import List, Optional

from src.common.logging import log_call, debug, info, error
from src.common.containers.container import Container
    
import subprocess
from src.common.logging import info, error
from src.features.website.utils import get_site_config
from src.common.utils.environment import env

@log_call
def get_php_container_name(domain: str) -> str:
    """
    Get the PHP container name for a domain.
    
    Args:
        domain: Website domain name
        
    Returns:
        PHP container name
    """
    return f"{domain}-php"


@log_call
def run_wp_cli(domain: str, args: List[str]) -> Optional[str]:
    """
    Execute WP-CLI command inside the PHP container for the domain.
    
    Args:
        domain: Website domain name
        args: List of WP-CLI command arguments, e.g. ['core', 'install', '--url=...', '--title=...']
        
    Returns:
        WP-CLI command output or None if error
    """
    container_name = get_php_container_name(domain)
    container = Container(name=container_name)

    if not container.running():
        error(f"❌ PHP container {container_name} is not running.")
        return None

    try:
        cmd = ["wp"] + args
        result = container.exec(cmd, workdir="/var/www/html")
        debug(f"WP CLI Output: {result}")
        return result
    except Exception as e:
        error(f"❌ Error executing WP-CLI: {e}")
        return None
    

WP_PATH_TEMPLATE = "/data/sites/{domain}/wordpress"

CACHE_PLUGINS = [
    "redis-cache", "wp-super-cache", "w3-total-cache", "wp-fastest-cache"
]

def get_wp_path(domain: str) -> str:
    # Lấy đường dẫn tuyệt đối tới thư mục wordpress của website trên host
    sites_dir = env.get("SITES_DIR")
    if not sites_dir:
        sites_dir = f"{env.get('INSTALL_DIR', '/opt/wp-docker')}/data/sites"
    return f"{sites_dir}/{domain}/wordpress"

def update_wp_config_cache(domain: str, cache_type: str) -> bool:
    wp_path = get_wp_path(domain)
    wp_config = f"{wp_path}/wp-config.php"
    try:
        with open(wp_config, "r") as f:
            lines = f.readlines()
        # Remove old WP_CACHE define
        lines = [l for l in lines if "define('WP_CACHE'" not in l]
        # Add new define at the top after <?php
        for i, l in enumerate(lines):
            if l.strip().startswith("<?php"):
                lines.insert(i+1, f"define('WP_CACHE', true); // {cache_type}\n")
                break
        with open(wp_config, "w") as f:
            f.writelines(lines)
        info(f"Updated wp-config.php for cache: {cache_type}")
        return True
    except Exception as e:
        error(f"Failed to update wp-config.php: {e}")
        return False

@log_call
def run_wpcli_in_wpcli_container(domain: str, args: List[str]) -> Optional[str]:
    """
    Execute WP-CLI command inside the WP CLI container for the domain.
    Args:
        domain: Website domain name
        args: List of WP-CLI command arguments, e.g. ['plugin', 'install', 'redis-cache', '--activate']
    Returns:
        WP-CLI command output or None if error
    """
    container_name = env["WPCLI_CONTAINER_NAME"]
    container = Container(name=container_name)
    if not container.running():
        error(f"❌ WP-CLI container {container_name} is not running.")
        return None
    wp_path = f"/var/www/html/{domain}/wordpress"
    try:
        cmd = ["wp"] + args
        result = container.exec(cmd, workdir=wp_path)
        debug(f"WP CLI (WPCLI container) Output: {result}")
        return result
    except Exception as e:
        error(f"❌ Error executing WP-CLI in WPCLI container: {e}")
        return None 

def deactivate_all_cache_plugins(domain: str) -> bool:
    """
    Deactivate all common cache plugins for a given WordPress domain using WP CLI container.
    """
    for plugin in CACHE_PLUGINS:
        result = run_wpcli_in_wpcli_container(domain, ["plugin", "deactivate", plugin])
        # Không fail nếu plugin không active, chỉ báo lỗi nếu có lỗi thực thi khác
        if result is None:
            error(f"Failed to deactivate {plugin} (may not be installed or another error)")
    info(f"Đã deactivate tất cả plugin cache phổ biến cho {domain}")
    return True 

def install_and_activate_plugin(domain: str, plugin_slug: str) -> bool:
    """
    Install and activate a plugin for a given WordPress domain using WP CLI container.
    """
    result = run_wpcli_in_wpcli_container(domain, ["plugin", "install", plugin_slug, "--activate"])
    if result is None:
        error(f"Failed to install/activate {plugin_slug}")
        return False
    info(f"Installed and activated plugin: {plugin_slug}")
    return True 

def get_active_plugins(domain: str) -> list:
    """
    Lấy danh sách các plugin đang active cho domain sử dụng WP CLI container.
    """
    result = run_wpcli_in_wpcli_container(domain, ["plugin", "list", "--status=active", "--field=name"])
    if result is None:
        return []
    return result.strip().splitlines() 
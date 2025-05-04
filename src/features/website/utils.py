"""
Website utility functions.

This module provides utility functions for working with websites,
including checking website status, listing websites, and managing website configurations.
"""

import os
import jsons
from typing import Dict, List, Optional, Any

from questionary import select

from src.common.logging import log_call, debug, info, warn, error
from src.common.config.manager import ConfigManager
from src.common.containers.container import Container
from src.common.utils.environment import env, env_required
from src.common.utils.system_info import get_total_cpu_cores, get_total_ram_mb


@log_call
def is_website_exists(domain: str) -> bool:
    """
    Check if a website exists both in filesystem and configuration.
    
    Args:
        domain: Website domain name
        
    Returns:
        True if website exists, False otherwise
    """
    config = ConfigManager()
    sites_dir = env["SITES_DIR"]
    site_dir = os.path.join(sites_dir, domain)
    site_dir_exists = os.path.isdir(site_dir)

    site_data = config.get().get("site", {})
    config_exists = domain in site_data  # Check if domain exists in site_data

    debug(f"site_dir_exists: {site_dir_exists}, config_exists: {config_exists}")
    return site_dir_exists and config_exists


@log_call
def is_website_running(domain: str) -> str:
    """
    Check if a website is running and return status message.
    
    Args:
        domain: Website domain name
        
    Returns:
        Status message indicating if website is running and why not if it isn't
    """
    if not is_website_exists(domain):
        return "❌ Invalid (missing directory or config)"

    try:
        php_container = Container(f"{domain}-php")
        if not php_container.running():
            return "❌ PHP container not running"
    except Exception as e:
        debug(f"Error checking PHP container: {e}")
        return "❌ PHP container error"

    try:
        nginx_conf = os.path.join(env["CONFIG_DIR"], "nginx", "conf.d", f"{domain}.conf")
        if not os.path.isfile(nginx_conf):
            return "❌ Missing NGINX configuration"
    except Exception as e:
        debug(f"Error checking NGINX config: {e}")
        return "❌ NGINX config error"

    return "✅ Running"


def calculate_php_fpm_values() -> Dict[str, Any]:
    """
    Calculate PHP-FPM settings based on server resources.
    
    Returns:
        Dictionary with calculated PHP-FPM configuration values
    """
    total_ram = get_total_ram_mb()  # MB
    total_cpu = get_total_cpu_cores()  # Number of cores

    # Determine server resource group
    is_low = total_cpu < 2 or total_ram < 2048
    is_high = total_cpu >= 8 and total_ram >= 8192
    is_medium = not is_low and not is_high

    # Set parameters according to resource group
    if is_low:
        reserved_ram = 384
        avg_process_size = 40
        pm_mode = "ondemand"
        cpu_multiplier = 3
    elif is_medium:
        reserved_ram = 512
        avg_process_size = 50
        pm_mode = "ondemand"
        cpu_multiplier = 5
    else:  # is_high
        reserved_ram = 1024
        avg_process_size = 60
        pm_mode = "dynamic"
        cpu_multiplier = 8

    available_ram = total_ram - reserved_ram
    ram_based_max = available_ram // avg_process_size
    cpu_based_max = total_cpu * cpu_multiplier
    max_children = min(ram_based_max, cpu_based_max)
    max_children = max(max_children, 4)

    if pm_mode == "dynamic":
        start_servers = min(total_cpu + 2, max_children)
        min_spare_servers = min(total_cpu, start_servers)
        max_spare_servers = min(total_cpu * 3, max_children)
    else:
        start_servers = 0
        min_spare_servers = 0
        max_spare_servers = min(total_cpu * 2, max_children)

    min_spare_servers = max(min_spare_servers, 1)
    max_spare_servers = max(max_spare_servers, 2)

    return {
        "pm_mode": pm_mode,
        "max_children": max_children,
        "start_servers": start_servers,
        "min_spare_servers": min_spare_servers,
        "max_spare_servers": max_spare_servers,
        "total_cpu": total_cpu,
        "total_ram": total_ram,
    }


def website_list() -> List[str]:
    """
    Get a list of all created websites.
    
    Returns:
        List of valid domain names
    """
    config = ConfigManager()
    raw_sites = config.get().get("site", {})
    debug(f"Website raw config: {raw_sites}")

    valid_domains = []
    for domain in raw_sites.keys():
        if is_website_exists(domain):
            valid_domains.append(domain)

    debug(f"Website valid domains: {valid_domains}")
    return valid_domains


def ensure_www_data_ownership(container_name: str, path_in_container: str) -> None:
    """
    Ensure www-data user owns the specified path in a container.
    
    Args:
        container_name: Name of the container
        path_in_container: Path inside the container
    """
    container = Container(name=container_name)
    debug(f"🔍 Checking ownership at {path_in_container} in container {container_name}")
    container.exec(["chown", "-R", "www-data:www-data", path_in_container], user="root")
    info(f"✅ Ensured www-data ownership for {path_in_container} in container {container_name}")


def get_site_config(domain: str) -> Optional[Any]:
    """
    Get configuration for a specific website.
    
    Args:
        domain: Website domain name
        
    Returns:
        Site configuration object or None if not found
    """
    # Import here to avoid circular imports
    from src.features.website.models.site_config import SiteConfig
    
    config = ConfigManager()
    raw_sites = config.get().get("site", {})
    site_raw = raw_sites.get(domain)
    if not site_raw:
        return None
    try:
        return jsons.load(site_raw, SiteConfig)
    except Exception as e:
        debug(f"❌ Error loading SiteConfig for {domain}: {e}")
        return None


def set_site_config(domain: str, site_config: Any) -> None:
    """
    Set configuration for a specific website.
    
    Args:
        domain: Website domain name
        site_config: Site configuration object
    """
    config = ConfigManager()
    site_data = config.get().get("site", {})
    site_data[domain] = jsons.dump(site_config, strict=True) 
    config.update_key("site", site_data)
    config.save()


def delete_site_config(domain: str, subkey: Optional[str] = None) -> bool:
    """
    Delete website configuration or a specific subkey.
    
    Args:
        domain: Website domain name
        subkey: Optional specific configuration key to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    config = ConfigManager()
    site_data = config.get().get("site", {})
    if domain not in site_data:
        return False

    if subkey:
        if subkey in site_data[domain]:
            del site_data[domain][subkey]
            config.update_key("site", site_data)
            config.save()
            return True
        return False
    else:
        # Delete the entire domain
        del site_data[domain]
        config.update_key("site", site_data)
        config.save()
        return True


def select_website(message: str = "Select website:", default: Optional[str] = None) -> Optional[str]:
    """
    Display a list of websites and allow selection.
    
    Args:
        message: Prompt message
        default: Default website to select
        
    Returns:
        Selected domain name or None if cancelled
    """
    websites = website_list()
    if not websites:
        warn("No websites found.")
        return None

    try:
        return select(
            message,
            choices=websites,
            default=default if default in websites else None
        ).ask()
    except (KeyboardInterrupt, EOFError):
        info("Operation cancelled.")
        return None


def get_sites_dir() -> str:
    """
    Get the directory containing all websites.
    
    Returns:
        Path to the sites directory
    """
    sites_dir = env["SITES_DIR"]
    if isinstance(sites_dir, dict):
        debug(f"Sites dir is a dictionary: {sites_dir}")
        sites_dir = sites_dir.get("path", "/opt/wp-docker/data/sites")
    return sites_dir
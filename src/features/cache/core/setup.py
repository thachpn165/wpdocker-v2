"""
Core logic for setting up cache (fastcgi-cache) for WordPress and configuring NGINX.
This module is designed for extensibility and separation of concerns.
"""

import os
import subprocess
from typing import Optional
from src.common.logging import info, error, success
from src.common.utils.validation import validate_domain
from src.features.cache.utils.cache import validate_cache_type
from src.features.cache.utils.nginx import update_nginx_cache_config
from src.features.cache.utils.wordpress import (
    deactivate_all_cache_plugins,
    install_and_activate_plugin,
    update_wp_config_cache,
    get_active_plugins,
)
from src.features.website.utils import get_site_config, set_site_config
from src.features.nginx.manager import reload as reload_nginx

CACHE_TYPE = "fastcgi-cache"
PLUGIN_SLUG = "redis-cache"
NGINX_CACHE_CONF_DIR = "/etc/nginx/cache/"


def setup_fastcgi_cache(domain: str) -> bool:
    """
    Set up fastcgi-cache for a WordPress site and configure NGINX.
    Args:
        domain: Domain name of the website
    Returns:
        bool: True if successful
    """
    # Validate domain
    if not validate_domain(domain):
        error(f"Invalid domain: {domain}")
        return False

    # Validate site config
    site_config = get_site_config(domain)
    if not site_config:
        error(f"Site configuration not found for {domain}")
        return False

    # Deactivate all cache plugins
    if not deactivate_all_cache_plugins(domain):
        error("Failed to deactivate existing cache plugins.")
        return False

    # Install and activate redis-cache plugin
    if not install_and_activate_plugin(domain, PLUGIN_SLUG):
        error(f"Failed to install/activate plugin: {PLUGIN_SLUG}")
        return False

    # Update wp-config.php for cache defines
    if not update_wp_config_cache(domain, CACHE_TYPE):
        error("Failed to update wp-config.php for cache.")
        return False

    # Update NGINX config to use fastcgi-cache
    if not update_nginx_cache_config(domain, CACHE_TYPE):
        error("Failed to update NGINX cache config.")
        return False

    # Reload NGINX
    if not reload_nginx():
        error("Failed to reload NGINX.")
        return False

    # Update site config metadata
    site_config.cache = CACHE_TYPE
    set_site_config(domain, site_config)

    success(f"✅ FastCGI cache successfully set up for {domain}")
    return True 
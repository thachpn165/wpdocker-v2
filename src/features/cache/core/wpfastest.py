"""
WP Fastest Cache setup logic for WordPress + NGINX.
Tách biệt để dễ mở rộng các loại cache khác.
"""
from src.common.logging import info, error, success
from src.common.utils.validation import is_valid_domain
from src.features.cache.utils.cache import validate_cache_type
from src.features.cache.utils.nginx import update_nginx_cache_config
from src.features.wordpress.utils import (
    deactivate_all_cache_plugins,
    install_and_activate_plugin,
    update_wp_config_cache,
)
from src.features.website.utils import get_site_config, set_site_config
from src.features.nginx.manager import reload as reload_nginx
from src.features.cache.constants import CACHE_PLUGINS, CACHE_SETUP_NOTICE
from src.common.webserver.utils import get_current_webserver


def print_cache_setup_notice(domain: str):
    print(CACHE_SETUP_NOTICE["wp-fastest-cache"].format(domain=domain))


def setup_wp_fastest_cache(domain: str) -> bool:
    """
    Set up WP Fastest Cache for a WordPress site and configure NGINX.
    Args:
        domain: Domain name of the website
    Returns:
        bool: True if successful
    """
    webserver = get_current_webserver()
    if webserver != "nginx":
        raise NotImplementedError(f"WP Fastest Cache setup is not implemented for webserver: {webserver}")

    # Validate domain
    if not is_valid_domain(domain):
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

    # Install and activate plugin
    for plugin_slug in CACHE_PLUGINS["wp-fastest-cache"]:
        if not install_and_activate_plugin(domain, plugin_slug):
            error(f"Failed to install/activate plugin: {plugin_slug}")
            return False

    # Update wp-config.php for cache defines (nếu cần, ở đây có thể không cần gì đặc biệt)
    if not update_wp_config_cache(domain, "wp-fastest-cache"):
        error("Failed to update wp-config.php for cache.")
        return False

    # Update NGINX config to use wp-fastest-cache
    if not update_nginx_cache_config(domain, "wp-fastest-cache"):
        error("Failed to update NGINX cache config.")
        return False

    # Reload NGINX
    if not reload_nginx():
        error("Failed to reload NGINX.")
        return False

    # Update site config metadata
    site_config.cache = "wp-fastest-cache"
    set_site_config(domain, site_config)

    success(f"✅ WP Fastest Cache successfully set up for {domain}")
    print_cache_setup_notice(domain)
    return True 
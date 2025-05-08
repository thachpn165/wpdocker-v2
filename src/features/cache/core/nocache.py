"""
No Cache logic for WordPress + NGINX.
Tắt toàn bộ các plugin cache và cấu hình NGINX về no-cache.
"""
from src.common.logging import info, error, success
from src.common.utils.validation import is_valid_domain
from src.features.cache.utils.cache import validate_cache_type
from src.features.cache.utils.nginx import update_nginx_cache_config
from src.features.wordpress.utils import deactivate_all_cache_plugins
from src.features.website.utils import get_site_config, set_site_config
from src.features.nginx.manager import reload as reload_nginx
from src.features.cache.constants import CACHE_SETUP_NOTICE


def print_cache_setup_notice(domain: str):
    print(CACHE_SETUP_NOTICE["no-cache"].format(domain=domain))


def setup_no_cache(domain: str) -> bool:
    """
    Disable all cache for a WordPress site and configure NGINX to no-cache.
    Args:
        domain: Domain name of the website
    Returns:
        bool: True if successful
    """
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

    # Update NGINX config to use no-cache
    if not update_nginx_cache_config(domain, "no-cache"):
        error("Failed to update NGINX cache config.")
        return False

    # Reload NGINX
    if not reload_nginx():
        error("Failed to reload NGINX.")
        return False

    # Update site config metadata
    site_config.cache = "no-cache"
    set_site_config(domain, site_config)

    success(f"✅ Đã tắt toàn bộ cache cho {domain}")
    print_cache_setup_notice(domain)
    return True 
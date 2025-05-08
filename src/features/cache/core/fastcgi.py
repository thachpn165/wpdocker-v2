"""
FastCGI cache setup logic for WordPress + NGINX.
Tách biệt để dễ mở rộng các loại cache khác.
"""
import subprocess
from src.common.logging import info, error, success
from src.common.utils.validation import is_valid_domain
from src.features.cache.utils.cache import validate_cache_type
from src.features.cache.utils.nginx import update_nginx_cache_config
from src.features.wordpress.utils import (
    deactivate_all_cache_plugins,
    install_and_activate_plugin,
    update_wp_config_cache,
    get_active_plugins,
    run_wpcli_in_wpcli_container,
)
from src.features.website.utils import get_site_config, set_site_config
from src.features.nginx.manager import reload as reload_nginx
from src.common.utils.environment import env
from src.features.wordpress.utils import get_wp_path
from src.features.cache.constants import CACHE_TYPES, CACHE_PLUGINS, CACHE_SETUP_NOTICE
from src.common.webserver.utils import get_current_webserver


def insert_redis_defines_to_wp_config(domain: str) -> bool:
    wp_path = get_wp_path(domain)
    wp_config = f"{wp_path}/wp-config.php"
    redis_host = env.get("REDIS_CONTAINER", "redis")
    defines = [
        f"define('WP_REDIS_HOST', '{redis_host}');\n",
        "define('WP_REDIS_PORT', 6379);\n",
        "define('WP_REDIS_DATABASE', 0);\n",
        "define('RT_WP_NGINX_HELPER_CACHE_PATH','/var/cache/nginx');\n"
    ]
    try:
        with open(wp_config, "r") as f:
            lines = f.readlines()
        # Xóa các dòng cũ nếu có
        lines = [l for l in lines if not l.strip().startswith("define('WP_REDIS_") and "RT_WP_NGINX_HELPER_CACHE_PATH" not in l]
        # Thêm sau <?php
        for i, l in enumerate(lines):
            if l.strip().startswith("<?php"):
                lines[i+1:i+1] = defines
                break
        with open(wp_config, "w") as f:
            f.writelines(lines)
        return True
    except Exception as e:
        error(f"Failed to update wp-config.php for redis: {e}")
        return False


def print_cache_setup_notice(domain: str):
    print(CACHE_SETUP_NOTICE["fastcgi-cache"].format(domain=domain))


def setup_fastcgi_cache(domain: str) -> bool:
    """
    Set up fastcgi-cache for a WordPress site and configure NGINX.
    Args:
        domain: Domain name of the website
    Returns:
        bool: True if successful
    """
    webserver = get_current_webserver()
    if webserver != "nginx":
        raise NotImplementedError(f"FastCGI cache setup is not implemented for webserver: {webserver}")

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

    # Install and activate plugins
    for plugin_slug in CACHE_PLUGINS["fastcgi-cache"]:
        if not install_and_activate_plugin(domain, plugin_slug):
            error(f"Failed to install/activate plugin: {plugin_slug}")
            return False

    # Update wp-config.php for cache defines
    if not update_wp_config_cache(domain, "fastcgi-cache"):
        error("Failed to update wp-config.php for cache.")
        return False

    # Update NGINX config to use fastcgi-cache
    if not update_nginx_cache_config(domain, "fastcgi-cache"):
        error("Failed to update NGINX cache config.")
        return False

    # Reload NGINX
    if not reload_nginx():
        error("Failed to reload NGINX.")
        return False

    # Update site config metadata
    site_config.cache = "fastcgi-cache"
    set_site_config(domain, site_config)

    # Thêm các dòng define vào wp-config.php
    if not insert_redis_defines_to_wp_config(domain):
        return False

    # Chạy lệnh WP CLI cấu hình redis object cache
    try:
        if run_wpcli_in_wpcli_container(domain, ["redis", "update-dropin"] ) is None:
            raise Exception("update-dropin failed")
        if run_wpcli_in_wpcli_container(domain, ["redis", "enable"] ) is None:
            raise Exception("enable failed")
    except Exception as e:
        error(f"Failed to configure redis object cache: {e}")
        return False

    success(f"✅ FastCGI cache successfully set up for {domain}")
    print_cache_setup_notice(domain)
    return True 
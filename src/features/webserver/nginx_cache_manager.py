from src.features.webserver.cache_manager import BaseCacheManager
from src.common.webserver.utils import get_current_webserver
from src.features.cache.constants import CACHE_PLUGINS, CACHE_SETUP_NOTICE
from src.features.website.utils import get_site_config, set_site_config
from src.features.wordpress.utils import (
    deactivate_all_cache_plugins,
    install_and_activate_plugin,
    update_wp_config_cache,
)
from src.common.logging import error, success
from src.common.utils.validation import is_valid_domain
from src.features.webserver.webserver_cache_config import update_webserver_cache_config
from src.features.webserver.webserver_reload import WebserverReload

class NginxCacheManager(BaseCacheManager):
    def setup_w3_total_cache(self, domain: str) -> bool:
        if not is_valid_domain(domain):
            error(f"Invalid domain: {domain}")
            return False
        site_config = get_site_config(domain)
        if not site_config:
            error(f"Site configuration not found for {domain}")
            return False
        if not deactivate_all_cache_plugins(domain):
            error("Failed to deactivate existing cache plugins.")
            return False
        for plugin_slug in CACHE_PLUGINS["w3-total-cache"]:
            if not install_and_activate_plugin(domain, plugin_slug):
                error(f"Failed to install/activate plugin: {plugin_slug}")
                return False
        if not update_wp_config_cache(domain, "w3-total-cache"):
            error("Failed to update wp-config.php for cache.")
            return False
        if not update_webserver_cache_config(domain, "w3-total-cache"):
            error("Failed to update webserver cache config.")
            return False
        if not WebserverReload.webserver_reload():
            error("Failed to reload webserver.")
            return False
        site_config.cache = "w3-total-cache"
        set_site_config(domain, site_config)
        success(f"✅ W3 Total Cache successfully set up for {domain}")
        print(CACHE_SETUP_NOTICE["w3-total-cache"].format(domain=domain))
        return True

    def setup_super_cache(self, domain: str) -> bool:
        if not is_valid_domain(domain):
            error(f"Invalid domain: {domain}")
            return False
        site_config = get_site_config(domain)
        if not site_config:
            error(f"Site configuration not found for {domain}")
            return False
        if not deactivate_all_cache_plugins(domain):
            error("Failed to deactivate existing cache plugins.")
            return False
        for plugin_slug in CACHE_PLUGINS["wp-super-cache"]:
            if not install_and_activate_plugin(domain, plugin_slug):
                error(f"Failed to install/activate plugin: {plugin_slug}")
                return False
        if not update_wp_config_cache(domain, "wp-super-cache"):
            error("Failed to update wp-config.php for cache.")
            return False
        if not update_webserver_cache_config(domain, "wp-super-cache"):
            error("Failed to update webserver cache config.")
            return False
        if not WebserverReload.webserver_reload():
            error("Failed to reload webserver.")
            return False
        site_config.cache = "wp-super-cache"
        set_site_config(domain, site_config)
        success(f"✅ WP Super Cache successfully set up for {domain}")
        print(CACHE_SETUP_NOTICE["wp-super-cache"].format(domain=domain))
        return True

    def setup_wp_fastest_cache(self, domain: str) -> bool:
        if not is_valid_domain(domain):
            error(f"Invalid domain: {domain}")
            return False
        site_config = get_site_config(domain)
        if not site_config:
            error(f"Site configuration not found for {domain}")
            return False
        if not deactivate_all_cache_plugins(domain):
            error("Failed to deactivate existing cache plugins.")
            return False
        for plugin_slug in CACHE_PLUGINS["wp-fastest-cache"]:
            if not install_and_activate_plugin(domain, plugin_slug):
                error(f"Failed to install/activate plugin: {plugin_slug}")
                return False
        if not update_wp_config_cache(domain, "wp-fastest-cache"):
            error("Failed to update wp-config.php for cache.")
            return False
        if not update_webserver_cache_config(domain, "wp-fastest-cache"):
            error("Failed to update webserver cache config.")
            return False
        if not WebserverReload.webserver_reload():
            error("Failed to reload webserver.")
            return False
        site_config.cache = "wp-fastest-cache"
        set_site_config(domain, site_config)
        success(f"✅ WP Fastest Cache successfully set up for {domain}")
        print(CACHE_SETUP_NOTICE["wp-fastest-cache"].format(domain=domain))
        return True

    def setup_no_cache(self, domain: str) -> bool:
        if not is_valid_domain(domain):
            error(f"Invalid domain: {domain}")
            return False
        site_config = get_site_config(domain)
        if not site_config:
            error(f"Site configuration not found for {domain}")
            return False
        if not deactivate_all_cache_plugins(domain):
            error("Failed to deactivate existing cache plugins.")
            return False
        if not update_webserver_cache_config(domain, "no-cache"):
            error("Failed to update webserver cache config.")
            return False
        if not WebserverReload.webserver_reload():
            error("Failed to reload webserver.")
            return False
        site_config.cache = "no-cache"
        set_site_config(domain, site_config)
        success(f"✅ Đã tắt toàn bộ cache cho {domain}")
        print(CACHE_SETUP_NOTICE["no-cache"].format(domain=domain))
        return True 
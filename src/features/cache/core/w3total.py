"""
W3 Total Cache setup logic for WordPress + NGINX.
Tách biệt để dễ mở rộng các loại cache khác.
"""
from src.common.logging import info, error, success
from src.common.utils.validation import is_valid_domain
from src.features.cache.utils.cache import validate_cache_type
from src.features.webserver.webserver_cache_config import update_webserver_cache_config
from src.features.webserver.webserver_reload import WebserverReload
from src.features.wordpress.utils import (
    deactivate_all_cache_plugins,
    install_and_activate_plugin,
    update_wp_config_cache,
)
from src.features.website.utils import get_site_config, set_site_config
from src.features.cache.constants import CACHE_PLUGINS, CACHE_SETUP_NOTICE
from src.common.webserver.utils import get_current_webserver
from src.features.webserver.cache_manager_factory import get_cache_manager


def print_cache_setup_notice(domain: str):
    print(CACHE_SETUP_NOTICE["w3-total-cache"].format(domain=domain))


def setup_w3_total_cache(domain: str) -> bool:
    result = get_cache_manager().setup_w3_total_cache(domain)
    if result:
        print_cache_setup_notice(domain)
    return result 
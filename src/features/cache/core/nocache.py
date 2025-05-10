"""
No Cache logic for WordPress + NGINX.
Tắt toàn bộ các plugin cache và cấu hình NGINX về no-cache.
"""
from src.common.logging import info, error, success
from src.common.utils.validation import is_valid_domain
from src.features.cache.utils.cache import validate_cache_type
from src.features.webserver.webserver_cache_config import update_webserver_cache_config
from src.features.wordpress.utils import deactivate_all_cache_plugins
from src.features.website.utils import get_site_config, set_site_config
from src.features.webserver.webserver_reload import WebserverReload
from src.features.cache.constants import CACHE_SETUP_NOTICE
from src.common.webserver.utils import get_current_webserver
from src.features.webserver.cache_manager_factory import get_cache_manager


def print_cache_setup_notice(domain: str):
    print(CACHE_SETUP_NOTICE["no-cache"].format(domain=domain))


def setup_no_cache(domain: str) -> bool:
    result = get_cache_manager().setup_no_cache(domain)
    if result:
        print_cache_setup_notice(domain)
    return result 
from src.common.webserver.utils import get_current_webserver
from src.features.webserver.nginx_cache_manager import NginxCacheManager

def get_cache_manager():
    webserver = get_current_webserver()
    if webserver == "nginx":
        return NginxCacheManager()
    # elif webserver == "apache":
    #     return ApacheCacheManager()
    else:
        raise NotImplementedError(f"Cache manager not implemented for webserver: {webserver}") 
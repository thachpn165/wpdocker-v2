from src.common.webserver.utils import get_current_webserver

def update_webserver_cache_config(domain: str, cache_type: str) -> bool:
    webserver = get_current_webserver()
    if webserver == "nginx":
        from src.features.cache.utils.nginx import update_nginx_cache_config
        return update_nginx_cache_config(domain, cache_type)
    # elif webserver == "apache":
    #     ... (implement logic for apache)
    else:
        raise NotImplementedError(f"Cache config update not implemented for webserver: {webserver}") 
from src.common.webserver.utils import get_current_webserver
from src.features.webserver.nginx_site_manager import NginxSiteManager

def get_site_manager():
    webserver = get_current_webserver()
    if webserver == "nginx":
        return NginxSiteManager()
    # elif webserver == "apache":
    #     return ApacheSiteManager()
    else:
        raise NotImplementedError(f"Webserver {webserver} not supported") 
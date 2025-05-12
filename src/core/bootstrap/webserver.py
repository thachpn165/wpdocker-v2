from src.common.webserver.utils import get_current_webserver
from src.core.bootstrap.nginx import NginxBootstrap


def get_webserver_bootstrap():
    webserver = get_current_webserver()
    if webserver == "nginx":
        return NginxBootstrap()
    # elif webserver == "apache":
    #     return ApacheBootstrap()
    else:
        raise NotImplementedError(f"Webserver {webserver} not supported")

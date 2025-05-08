from src.common.webserver.utils import get_current_webserver

if get_current_webserver() == "nginx":
    from src.features.nginx.manager import reload as nginx_reload

class WebserverReload:
    @staticmethod
    def webserver_reload():
        webserver = get_current_webserver()
        if webserver == "nginx":
            return nginx_reload()
        # elif webserver == "apache":
        #     ...
        else:
            raise NotImplementedError(f"Reload not supported for webserver: {webserver}") 
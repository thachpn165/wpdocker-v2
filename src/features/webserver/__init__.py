"""
Web server module integration.

This module serves as a compatibility layer to load the appropriate web server module
based on the system configuration. Currently, it supports NGINX by default.
"""
# This is a compatibility layer for future web server support
# It will automatically load the configured web server module

from src.common.webserver.utils import get_current_webserver
import subprocess

try:
    webserver_type = get_current_webserver()
except ValueError:
    # Default to NGINX if not configured
    webserver_type = "nginx"

# Load appropriate web server module
if webserver_type == "nginx":
    from src.features.nginx import test_config, reload, restart
    from src.features.nginx.manager import apply_config
    
    # Export functions
    __all__ = ['test_config', 'reload', 'restart', 'apply_config']
else:
    # Placeholder for future web server support
    def not_implemented(*args, **kwargs):
        raise NotImplementedError(f"Web server '{webserver_type}' not supported yet")
        
    test_config = reload = restart = apply_config = not_implemented
    
    __all__ = ['test_config', 'reload', 'restart', 'apply_config']

class WebserverReload:
    @staticmethod
    def webserver_reload():
        webserver = get_current_webserver()
        if webserver == "nginx":
            # Reload nginx (bạn có thể điều chỉnh lệnh này cho phù hợp môi trường Docker/local)
            try:
                subprocess.run(["docker", "exec", "nginx", "nginx", "-s", "reload"], check=True)
            except Exception:
                # Nếu không chạy trong docker/nginx container, thử lệnh hệ thống
                subprocess.run(["nginx", "-s", "reload"], check=True)
        # Có thể mở rộng cho các webserver khác
        # elif webserver == "apache":
        #     subprocess.run(["systemctl", "reload", "apache2"], check=True)
        else:
            raise NotImplementedError(f"Reload not supported for webserver: {webserver}")
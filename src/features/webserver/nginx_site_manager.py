import os
from src.features.webserver.site_manager import WebserverSiteManager
from src.common.utils.environment import env
from src.features.nginx.manager import restart as nginx_restart

class NginxSiteManager(WebserverSiteManager):
    def create_website(self, domain: str, **kwargs) -> bool:
        install_dir = env["INSTALL_DIR"]
        nginx_template = os.path.join(
            install_dir, "src", "templates", "nginx", "nginx-vhost.conf.template")
        nginx_target_dir = os.path.join(env["CONFIG_DIR"], "nginx", "conf.d")
        nginx_target_path = os.path.join(nginx_target_dir, f"{domain}.conf")
        os.makedirs(nginx_target_dir, exist_ok=True)
        if os.path.isfile(nginx_template):
            with open(nginx_template, "r") as f:
                content = f.read().replace("${DOMAIN}", domain)
            with open(nginx_target_path, "w") as f:
                f.write(content)
            nginx_restart()
            return True
        return False

    def delete_website(self, domain: str) -> bool:
        nginx_target_path = os.path.join(
            env["CONFIG_DIR"], "nginx", "conf.d", f"{domain}.conf")
        if os.path.isfile(nginx_target_path):
            os.remove(nginx_target_path)
            from src.common.logging import info
            info(f"🗑️ Removed NGINX vhost file for {domain}")
            return True
        return False

    def ensure_site_config(self, domain: str) -> bool:
        nginx_target_path = os.path.join(
            env["CONFIG_DIR"], "nginx", "conf.d", f"{domain}.conf")
        return os.path.isfile(nginx_target_path) 
import os
import subprocess
from src.common.logging import info, error

NGINX_CONF_DIR = "/etc/nginx/conf.d/"
NGINX_CACHE_INCLUDE = "/etc/nginx/cache/"
NGINX_CONTAINER = "nginx"  # Tên container, có thể lấy từ env/config nếu cần


def update_nginx_cache_config(domain: str, cache_type: str) -> bool:
    """
    Update NGINX config file for the domain to use the specified cache_type.
    """
    conf_file = os.path.join(NGINX_CONF_DIR, f"{domain}.conf")
    include_line = f"include {NGINX_CACHE_INCLUDE}{cache_type}.conf;"
    try:
        if not os.path.exists(conf_file):
            error(f"NGINX config file not found: {conf_file}")
            return False
        with open(conf_file, "r") as f:
            lines = f.readlines()
        found = False
        for i, l in enumerate(lines):
            if l.strip().startswith("include ") and "/cache/" in l:
                lines[i] = include_line + "\n"
                found = True
                break
        if not found:
            # Thêm vào cuối file nếu chưa có
            lines.append(include_line + "\n")
        with open(conf_file, "w") as f:
            f.writelines(lines)
        info(f"Updated NGINX config for {domain} to use cache: {cache_type}")
        return True
    except Exception as e:
        error(f"Failed to update NGINX config: {e}")
        return False

def reload_nginx() -> bool:
    """
    Reload NGINX inside the container.
    """
    try:
        result = subprocess.run(["docker", "exec", NGINX_CONTAINER, "nginx", "-s", "reload"], capture_output=True, text=True)
        if result.returncode == 0:
            info("Reloaded NGINX successfully.")
            return True
        else:
            error(f"NGINX reload failed: {result.stderr}")
            return False
    except Exception as e:
        error(f"Error reloading NGINX: {e}")
        return False 
import os
import subprocess
from src.common.logging import info, error
from src.common.utils.environment import env

# Không dùng NGINX_CONF_DIR và NGINX_CACHE_INCLUDE hard code nữa
# NGINX_HOST_CONFIG_FILE sẽ lấy từ env


def update_nginx_cache_config(domain: str, cache_type: str) -> bool:
    """
    Update NGINX config file for the domain to use the specified cache_type.
    Sử dụng đường dẫn file trên host lấy từ biến môi trường NGINX_HOST_CONFIG_FILE.
    """
    conf_file = env.get("NGINX_HOST_CONFIG_FILE")
    if not conf_file:
        error("NGINX_HOST_CONFIG_FILE is not set in environment.")
        return False
    include_line = f"include /etc/nginx/cache/{cache_type}.conf;"
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
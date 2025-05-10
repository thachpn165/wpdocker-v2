import os
import subprocess
from src.common.logging import info, error
from src.common.utils.environment import env

# Không dùng NGINX_CONF_DIR và NGINX_CACHE_INCLUDE hard code nữa
# NGINX_HOST_CONFIG_FILE sẽ lấy từ env


def update_nginx_cache_config(domain: str, cache_type: str) -> bool:
    """
    Update NGINX vhost config file for the domain to use the specified cache_type.
    Sử dụng đường dẫn file vhost lấy từ biến môi trường NGINX_HOST_VHOST_CONF + /<domain>.conf.
    """
    vhost_dir = env.get("NGINX_HOST_VHOST_CONF")
    if not vhost_dir:
        error("NGINX_HOST_VHOST_CONF is not set in environment.")
        return False
    vhost_file = os.path.join(vhost_dir, f"{domain}.conf")
    include_line = f"include /usr/local/openresty/nginx/conf/cache/{cache_type}.conf;"
    try:
        if not os.path.exists(vhost_file):
            error(f"NGINX vhost config file not found: {vhost_file}")
            return False
        with open(vhost_file, "r") as f:
            lines = f.readlines()
        found = False
        for i, l in enumerate(lines):
            if l.strip().startswith("include ") and "/nginx/conf/cache/" in l:
                lines[i] = include_line + "\n"
                found = True
                break
        if not found:
            # Thêm vào cuối file nếu chưa có
            lines.append(include_line + "\n")
        with open(vhost_file, "w") as f:
            f.writelines(lines)
        info(f"Updated NGINX vhost config for {domain} to use cache: {cache_type}")
        return True
    except Exception as e:
        error(f"Failed to update NGINX vhost config: {e}")
        return False 
"""
WordPress utility functions.

This module provides utility functions for WordPress operations,
including WP-CLI command execution, protection features, and other utilities.
"""

from typing import List, Optional, Tuple
import os
from passlib.hash import apr_md5_crypt

from src.common.logging import log_call, debug, info, error, success
from src.common.containers.container import Container
from src.common.utils.environment import env
from src.common.utils.password import strong_password
from src.features.cache.constants import CACHE_PLUGINS as CACHE_PLUGINS_DICT
from src.common.webserver.utils import get_current_webserver


@log_call
def get_php_container_name(domain: str) -> str:
    """
    Get the PHP container name for a domain.

    Args:
        domain: Website domain name

    Returns:
        PHP container name
    """
    return f"{domain}-php"


@log_call
def run_wp_cli(domain: str, args: List[str]) -> Optional[str]:
    """
    Execute WP-CLI command inside the PHP container for the domain.

    Args:
        domain: Website domain name
        args: List of WP-CLI command arguments, e.g. ['core', 'install', '--url=...', '--title=...']

    Returns:
        WP-CLI command output or None if error
    """
    container_name = get_php_container_name(domain)
    container = Container(name=container_name)

    if not container.running():
        error(f"❌ PHP container {container_name} is not running.")
        return None

    try:
        cmd = ["wp"] + args
        result = container.exec(cmd, workdir="/var/www/html")
        debug(f"WP CLI Output: {result}")
        return result
    except Exception as e:
        error(f"❌ Error executing WP-CLI: {e}")
        return None


WP_PATH_TEMPLATE = "/data/sites/{domain}/wordpress"

CACHE_PLUGINS = [
    "redis-cache", "wp-super-cache", "w3-total-cache", "wp-fastest-cache"
]


def get_wp_path(domain: str) -> str:
    # Lấy đường dẫn tuyệt đối tới thư mục wordpress của website trên host
    sites_dir = env.get("SITES_DIR")
    if not sites_dir:
        sites_dir = f"{env.get('INSTALL_DIR', '/opt/wp-docker')}/data/sites"
    return f"{sites_dir}/{domain}/wordpress"


def update_wp_config_cache(domain: str, cache_type: str) -> bool:
    wp_path = get_wp_path(domain)
    wp_config = f"{wp_path}/wp-config.php"
    try:
        with open(wp_config, "r") as f:
            lines = f.readlines()
        # Remove old WP_CACHE define
        lines = [line for line in lines if "define('WP_CACHE'" not in line]
        # Add new define at the top after <?php
        for i, line in enumerate(lines):
            if line.strip().startswith("<?php"):
                lines.insert(
                    i + 1, f"define('WP_CACHE', true); // {cache_type}\n")
                break
        with open(wp_config, "w") as f:
            f.writelines(lines)
        info(f"Updated wp-config.php for cache: {cache_type}")
        return True
    except Exception as e:
        error(f"Failed to update wp-config.php: {e}")
        return False


@log_call
def run_wpcli_in_wpcli_container(domain: str, args: List[str]) -> Optional[str]:
    """
    Execute WP-CLI command inside the WP CLI container for the domain.
    Args:
        domain: Website domain name
        args: List of WP-CLI command arguments, e.g. ['plugin', 'install', 'redis-cache', '--activate']
    Returns:
        WP-CLI command output or None if error
    """
    container_name = env["WPCLI_CONTAINER_NAME"]
    container = Container(name=container_name)
    if not container.running():
        error(f"❌ WP-CLI container {container_name} is not running.")
        return None
    wp_path = f"/var/www/html/{domain}/wordpress"
    try:
        cmd = ["wp"] + args
        result = container.exec(cmd, workdir=wp_path, user="www-data")
        debug(f"WP CLI (WPCLI container) Output: {result}")
        return result
    except Exception as e:
        error(f"❌ Error executing WP-CLI in WPCLI container: {e}")
        return None


def deactivate_all_cache_plugins(domain: str) -> bool:
    """
    Deactivate all common cache plugins for a given WordPress domain using WP CLI container.
    Chỉ deactivate nếu plugin cache thực sự đang active.
    """
    # Lấy danh sách plugin cache từ constants (dạng dict)
    cache_plugin_slugs = set()
    for v in CACHE_PLUGINS_DICT.values():
        cache_plugin_slugs.update(v)
    # Lấy danh sách plugin đang active
    active_plugins = set(get_active_plugins(domain))
    # Lọc ra các plugin cache đang active
    active_cache_plugins = active_plugins.intersection(cache_plugin_slugs)
    if not active_cache_plugins:
        info(f"Không có plugin cache nào đang active cho {domain}")
        return True
    for plugin in active_cache_plugins:
        result = run_wpcli_in_wpcli_container(
            domain, ["plugin", "deactivate", plugin])
        if result is None:
            error(
                f"Failed to deactivate {plugin} (may not be installed or another error)")
    info(
        f"Đã deactivate các plugin cache đang active cho {domain}: {', '.join(active_cache_plugins)}")
    return True


def install_and_activate_plugin(domain: str, plugin_slug: str) -> bool:
    """
    Install and activate a plugin for a given WordPress domain using WP CLI container.
    """
    result = run_wpcli_in_wpcli_container(
        domain, ["plugin", "install", plugin_slug, "--activate"])
    if result is None:
        error(f"Failed to install/activate {plugin_slug}")
        return False
    info(f"Installed and activated plugin: {plugin_slug}")
    return True


def get_active_plugins(domain: str) -> list:
    """
    Lấy danh sách các plugin đang active cho domain sử dụng WP CLI container.
    """
    result = run_wpcli_in_wpcli_container(
        domain, ["plugin", "list", "--status=active", "--field=name"])
    if result is None:
        return []
    return result.strip().splitlines()


def get_htpasswd_path(domain: str) -> str:
    """
    Lấy đường dẫn tới file .htpasswd của domain trên host.
    Args:
        domain: Tên miền website
    Returns:
        Đường dẫn tuyệt đối đến file .htpasswd
    """
    sites_dir = env.get("SITES_DIR")
    if not sites_dir:
        sites_dir = f"{env.get('INSTALL_DIR', '/opt/wp-docker')}/data/sites"
    return f"{sites_dir}/{domain}/.htpasswd"


@log_call
def generate_htpasswd_hash(password: str) -> str:
    """
    Sinh hash APR1-MD5 đúng chuẩn cho file .htpasswd (dùng cho NGINX/Apache).
    """
    return apr_md5_crypt.hash(password)


@log_call
def create_or_update_htpasswd(domain: str, username: str = "admin") -> Tuple[str, str]:
    """
    Tạo hoặc cập nhật file .htpasswd cho bảo vệ wp-login.php.
    Args:
        domain: Tên miền website
        username: Tên người dùng để đăng nhập, mặc định là 'admin'
    Returns:
        Tuple chứa (username, password) đã tạo
    """
    htpasswd_path = get_htpasswd_path(domain)
    password = strong_password()
    password_hash = generate_htpasswd_hash(password)
    # Tạo thư mục cha nếu chưa tồn tại
    os.makedirs(os.path.dirname(htpasswd_path), exist_ok=True)
    # Ghi file .htpasswd
    with open(htpasswd_path, 'w') as f:
        f.write(f"{username}:{password_hash}\n")
    success(f"✅ Đã tạo file .htpasswd tại {htpasswd_path}")
    return username, password


@log_call
def delete_htpasswd(domain: str) -> bool:
    """
    Xóa file .htpasswd của domain.
    Args:
        domain: Tên miền website
    Returns:
        True nếu xóa thành công hoặc file không tồn tại, False nếu có lỗi
    """
    htpasswd_path = get_htpasswd_path(domain)
    if os.path.exists(htpasswd_path):
        try:
            os.remove(htpasswd_path)
            info(f"🗑️ Đã xóa file .htpasswd tại {htpasswd_path}")
        except Exception as e:
            error(f"❌ Không thể xóa file .htpasswd: {e}")
            return False
    return True


def get_nginx_site_path(domain: str) -> str:
    """
    Lấy đường dẫn tới thư mục nginx của domain.

    Args:
        domain: Tên miền website

    Returns:
        Đường dẫn tuyệt đối đến thư mục nginx của domain
    """
    sites_dir = env.get("SITES_DIR")
    if not sites_dir:
        sites_dir = f"{env.get('INSTALL_DIR', '/opt/wp-docker')}/data/sites"
    return f"{sites_dir}/{domain}/nginx"


@log_call
def init_config_wplogin_protection(domain: str) -> bool:
    """
    Tạo hoặc cập nhật file cấu hình bảo vệ wp-login.php cho webserver hiện tại (nginx, apache, ...).
    Args:
        domain: Tên miền website
    Returns:
        True nếu cập nhật thành công, False nếu có lỗi
    """
    try:
        webserver = get_current_webserver()
        install_dir = env.get("INSTALL_DIR", "/opt/wp-docker")
        template_path = None
        target_path = None
        # htpasswd_path_host = get_htpasswd_path(domain)
        htpasswd_path_container = f"/var/www/{domain}/.htpasswd"
        if webserver == "nginx":
            template_path = os.path.join(
                install_dir, "src", "templates", "nginx", "protect-wplogin-domain.conf.template")
            nginx_dir = get_nginx_site_path(domain)
            target_path = os.path.join(nginx_dir, "protect-wplogin.conf")
        elif webserver == "apache":
            template_path = os.path.join(
                install_dir, "src", "templates", "apache", "protect-wplogin-domain.conf.template")
            apache_dir = os.path.join(
                env.get("SITES_DIR", f"{install_dir}/data/sites"), domain, "apache")
            os.makedirs(apache_dir, exist_ok=True)
            target_path = os.path.join(apache_dir, "protect-wplogin.conf")
        else:
            error(f"❌ Chưa hỗ trợ webserver: {webserver}")
            return False
        if not os.path.exists(template_path):
            error(
                f"❌ Không tìm thấy template bảo vệ wp-login.php cho webserver: {webserver} ({template_path})")
            return False
        # Tạo thư mục đích nếu chưa tồn tại
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        # Đọc nội dung template
        with open(template_path, "r") as f:
            content = f.read()
        # Thay thế biến
        content = content.replace(
            "${domain_htpasswd_file}", htpasswd_path_container)
        # Ghi file cấu hình
        with open(target_path, "w") as f:
            f.write(content)
        success(
            f"✅ Đã tạo file cấu hình bảo vệ wp-login.php cho {webserver} tại {target_path}")
        return True
    except Exception as e:
        error(f"❌ Không thể tạo file cấu hình bảo vệ wp-login.php: {e}")
        return False


@log_call
def delete_wplogin_protection(domain: str) -> bool:
    """
    Xóa file cấu hình bảo vệ wp-login.php của domain cho webserver hiện tại (nginx, apache, ...).

    Args:
        domain: Tên miền website

    Returns:
        True nếu xóa thành công hoặc file không tồn tại, False nếu có lỗi
    """
    try:
        webserver = get_current_webserver()
        install_dir = env.get("INSTALL_DIR", "/opt/wp-docker")
        target_path = None
        if webserver == "nginx":
            nginx_dir = get_nginx_site_path(domain)
            target_path = os.path.join(nginx_dir, "protect-wplogin.conf")
        elif webserver == "apache":
            apache_dir = os.path.join(
                env.get("SITES_DIR", f"{install_dir}/data/sites"), domain, "apache")
            target_path = os.path.join(apache_dir, "protect-wplogin.conf")
        else:
            error(f"❌ Chưa hỗ trợ webserver: {webserver}")
            return False

        if target_path and os.path.exists(target_path):
            try:
                os.remove(target_path)
                info(
                    f"🗑️ Đã xóa file cấu hình bảo vệ wp-login.php cho {webserver} tại {target_path}")
            except Exception as e:
                error(
                    f"❌ Không thể xóa file cấu hình bảo vệ wp-login.php: {e}")
                return False
        else:
            info(
                f"ℹ️ Không tìm thấy file cấu hình bảo vệ wp-login.php cho {webserver} tại {target_path}")
        return True
    except Exception as e:
        error(f"❌ Lỗi khi xóa file cấu hình bảo vệ wp-login.php: {e}")
        return False


def add_protect_include_to_vhost(domain: str) -> bool:
    """
    Thêm dòng include protect-wplogin.conf vào file vhost của domain (chỉ hỗ trợ NGINX).
    """
    from src.common.webserver.utils import get_current_webserver
    webserver = get_current_webserver()
    if webserver != "nginx":
        raise NotImplementedError("Chỉ hỗ trợ tự động chèn include cho NGINX")
    vhost_dir = env.get("NGINX_HOST_VHOST_CONF")
    if not vhost_dir:
        error("NGINX_HOST_VHOST_CONF is not set in environment.")
        return False
    vhost_file = os.path.join(vhost_dir, f"{domain}.conf")
    include_line = f"include /var/www/{domain}/nginx/protect-wplogin.conf;"
    try:
        if not os.path.exists(vhost_file):
            error(f"NGINX vhost config file not found: {vhost_file}")
            return False
        with open(vhost_file, "r") as file:
            lines = file.readlines()
        if any(include_line in line for line in lines):
            info(
                f"Dòng include bảo vệ wp-login.php đã tồn tại trong {vhost_file}")
            return True
        # Tìm vị trí '}' cuối cùng
        insert_idx = None
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '}':
                insert_idx = i
                break
        if insert_idx is not None:
            lines.insert(insert_idx, include_line + "\n")
        else:
            lines.append(include_line + "\n")
        with open(vhost_file, "w") as f:
            f.writelines(lines)
        success(f"Đã thêm include bảo vệ wp-login.php vào {vhost_file}")
        return True
    except Exception as e:
        error(f"Lỗi khi thêm include bảo vệ wp-login.php: {e}")
        return False


def remove_protect_include_from_vhost(domain: str) -> bool:
    """
    Xóa dòng include protect-wplogin.conf khỏi file vhost của domain (chỉ hỗ trợ NGINX).
    """
    from src.common.webserver.utils import get_current_webserver
    webserver = get_current_webserver()
    if webserver != "nginx":
        raise NotImplementedError("Chỉ hỗ trợ tự động xóa include cho NGINX")
    vhost_dir = env.get("NGINX_HOST_VHOST_CONF")
    if not vhost_dir:
        error("NGINX_HOST_VHOST_CONF is not set in environment.")
        return False
    vhost_file = os.path.join(vhost_dir, f"{domain}.conf")
    include_line = f"include /var/www/{domain}/nginx/protect-wplogin.conf;"
    try:
        if not os.path.exists(vhost_file):
            error(f"NGINX vhost config file not found: {vhost_file}")
            return False
        with open(vhost_file, "r") as file:
            lines = file.readlines()
        updated_lines = [line for line in lines if include_line not in line]
        if len(updated_lines) == len(lines):
            info(
                f"Không tìm thấy dòng include bảo vệ wp-login.php trong {vhost_file}")
            return True
        with open(vhost_file, "w") as f:
            f.writelines(updated_lines)
        success(f"Đã xóa include bảo vệ wp-login.php khỏi {vhost_file}")
        return True
    except Exception as e:
        error(f"Lỗi khi xóa include bảo vệ wp-login.php: {e}")
        return False


def show_wp_user_list(domain: str) -> None:
    """
    Hiển thị danh sách user qua WP-CLI.
    """
    result = run_wpcli_in_wpcli_container(
        domain, ["user", "list", "--format=table"])
    if result:
        print(result)
    else:
        print("Không thể lấy danh sách user.")


def reset_wp_user_password(domain: str, user_id: str) -> Optional[str]:
    """
    Reset password cho user_id, trả về mật khẩu mới nếu thành công.
    """
    result = run_wpcli_in_wpcli_container(
        domain, ["user", "reset-password", user_id,
                 "--show-password", "--porcelain"]
    )
    if result:
        return result.strip()
    return None


def get_wp_user_info(domain: str, user_id: str) -> Optional[dict]:
    """
    Lấy thông tin user (username, email, role, ...) theo user_id qua WP-CLI.
    """
    result = run_wpcli_in_wpcli_container(
        domain, ["user", "get", user_id, "--format=json"]
    )
    if result:
        import json
        try:
            return json.loads(result)
        except Exception:
            return None
    return None


def get_wp_roles(domain: str) -> list:
    """
    Lấy danh sách role của website qua WP-CLI.
    """
    result = run_wpcli_in_wpcli_container(
        domain, ["role", "list", "--format=json"])
    if result:
        import json
        try:
            return json.loads(result)
        except Exception:
            return []
    return []


def reset_wp_user_role(domain: str, role: Optional[str] = None, all_roles: bool = False) -> bool:
    """
    Reset user role cho website. Nếu all_roles=True thì reset tất cả roles.
    """
    args = ["role", "reset"]
    if all_roles:
        args.append("--all")
    elif role:
        args.append(role)
    else:
        return False
    result = run_wpcli_in_wpcli_container(domain, args)
    return result is not None

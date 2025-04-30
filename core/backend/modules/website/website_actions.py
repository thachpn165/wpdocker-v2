from core.backend.modules.mysql.database import setup_database_for_website, delete_database, delete_database_user
from core.backend.utils.debug import info, warn, error, debug, log_call
from core.backend.utils.env_utils import env
from core.backend.objects.config import Config
from core.backend.objects.compose import Compose
from core.backend.modules.ssl.install import install_selfsigned_ssl
from core.backend.modules.nginx.nginx import restart as nginx_restart
from core.backend.objects.container import Container
from core.backend.modules.website.website_utils import website_calculate_php_fpm_values

import os
import shutil

@log_call
def setup_directories(domain):
    """Tạo cấu trúc thư mục cơ bản cho website"""
    sites_dir = env["SITES_DIR"]
    site_dir = os.path.join(sites_dir, domain)

    os.makedirs(os.path.join(site_dir, "php"), exist_ok=True)
    os.makedirs(os.path.join(site_dir, "wordpress"), exist_ok=True)
    os.makedirs(os.path.join(site_dir, "logs"), exist_ok=True)
    os.makedirs(os.path.join(site_dir, "backups"), exist_ok=True)
    os.makedirs(os.path.join(site_dir, "ssl"), exist_ok=True)

    for log_file in ["access.log", "error.log", "php_error.log", "php_slow.log"]:
        log_path = os.path.join(site_dir, "logs", log_file)
        open(log_path, "a").close()
        os.chmod(log_path, 0o666)


def cleanup_directories(domain):
    """Xóa toàn bộ thư mục website"""
    sites_dir = env["SITES_DIR"]
    site_dir = os.path.join(sites_dir, domain)
    if os.path.isdir(site_dir):
        shutil.rmtree(site_dir)
        info(f"🗑️ Đã xóa thư mục {site_dir}")

@log_call
def setup_config(domain, php_version):
    """Ghi cấu hình website vào config.json"""
    config = Config()
    sites_dir = env["SITES_DIR"]
    logs_dir = os.path.join(sites_dir, domain, "logs")

    # Lấy dữ liệu hiện tại (sẽ luôn là dict)
    current_sites = config.get("site", {}) or {}

    # Lấy container ID của PHP
    php_container_name = f"{domain}-php"
    container = Container(name=php_container_name)
    container_id = container.get().id if container.get() else None

    # Chèn hoặc cập nhật đúng domain
    site_data = current_sites.get(domain, {})
    site_data["domain"] = domain
    site_data["php_version"] = php_version
    site_data["logs"] = {
        "access": os.path.join(logs_dir, "access.log"),
        "error": os.path.join(logs_dir, "error.log"),
        "php_error": os.path.join(logs_dir, "php_error.log"),
        "php_slow": os.path.join(logs_dir, "php_slow.log")
    }
    if container_id:
        site_data["php_container_id"] = container_id

    current_sites[domain] = site_data
    config.set("site", current_sites, split_path=False)
    config.save()
    info(f"✅ Đã lưu thông tin website {domain} vào config.json")


def cleanup_config(domain):
    """Xóa cấu hình website khỏi config.json"""
    config = Config()
    current_sites = config.get("site", {})
    if domain in current_sites:
        del current_sites[domain]
        config.set("site", current_sites, split_path=False)
        config.save()
        info(f"🗑️ Đã xóa config website {domain} khỏi config.json")


def setup_php_configs(domain, php_version):
    """Tạo file php.ini và php-fpm.conf"""
    sites_dir = env["SITES_DIR"]
    site_dir = os.path.join(sites_dir, domain)
    install_dir = env["INSTALL_DIR"]
    php_ini_template = os.path.join(
        install_dir, "core", "templates", "php.ini.template")
    timezone = Config().get("core.timezone", "UTC")

    php_ini_target = os.path.join(site_dir, "php", "php.ini")
    if os.path.isfile(php_ini_template):
        with open(php_ini_template, "r") as f:
            content = f.read().replace("${TIMEZONE}", timezone)
        with open(php_ini_target, "w") as f:
            f.write(content)

    fpm_values = website_calculate_php_fpm_values()
    php_fpm_conf_path = os.path.join(site_dir, "php", "php-fpm.conf")
    with open(php_fpm_conf_path, "w") as f:
        f.write(f"""[www]
user = www-data
group = www-data
listen = 9000
pm = {fpm_values['pm_mode']}
pm.max_children = {fpm_values['max_children']}
pm.start_servers = {fpm_values['start_servers']}
pm.min_spare_servers = {fpm_values['min_spare_servers']}
pm.max_spare_servers = {fpm_values['max_spare_servers']}
pm.process_idle_timeout = 10s
pm.max_requests = 1000
slowlog=/var/www/logs/php_slow.log
request_slowlog_timeout = 10
request_terminate_timeout = 60
""")


def cleanup_php_configs(domain):
    """Không cần riêng vì xóa thư mục là đã xóa rồi"""

@log_call
def setup_compose_php(domain, php_version):
    """Tạo docker-compose cho PHP"""
    install_dir = env["INSTALL_DIR"]
    sites_dir = env["SITES_DIR"]
    site_dir = os.path.join(sites_dir, domain)

    docker_compose_template = os.path.join(
        install_dir, "core", "templates", "docker-compose.php.yml.template")
    docker_compose_target = os.path.join(site_dir, "docker-compose.php.yml")
    php_container = f"{domain}-php"

    if os.path.isfile(docker_compose_template):
        with open(docker_compose_template, "r") as f:
            content = f.read()
        content = content.replace("${php_container}", php_container)
        content = content.replace("${php_version}", php_version)
        content = content.replace("${PROJECT_NAME}", env["PROJECT_NAME"])
        content = content.replace(
            "${CORE_DIR}", os.path.join(install_dir, "core"))
        content = content.replace("${DOCKER_NETWORK}", env["DOCKER_NETWORK"])
        content = content.replace("${domain}", domain)

        with open(docker_compose_target, "w") as f:
            f.write(content)

    compose = Compose(
        template_path=docker_compose_template,
        output_path=docker_compose_target,
        env_map={
            "PROJECT_NAME": env["PROJECT_NAME"],
            "CORE_DIR": os.path.join(install_dir, "core"),
            "DOCKER_NETWORK": env["DOCKER_NETWORK"],
            "domain": domain,
            "php_container": php_container,
            "php_version": php_version
        },
        name=php_container
    )
    compose.ensure_ready()

    # Chown thư mục /var/www/<domain> trong container PHP
    container = Container(name=php_container)
    container.exec(["chown", "-R", "www-data:www-data", f"/var/www/html"], user="root")
    debug(f"✅ Đã phân quyền www-data cho thư mục /var/www/html trong container {php_container}")



@log_call(log_vars=["domain", "site_data", "container_id"])
def cleanup_compose_php(domain):
    """Xóa docker-compose PHP và container PHP tương ứng"""
    config = Config()
    site_data = config.get("site", {}, split_path=False).get(domain)
    container_id = site_data.get("php_container_id") if site_data else None
    if container_id:
        container = Container(name=container_id)
        if container.exists():
            debug(f"Đang dừng và xóa container {container_id}...")
            container.stop()
            container.remove()

    docker_compose_target = os.path.join(
        env["SITES_DIR"], domain, "docker-compose.php.yml")
    if os.path.isfile(docker_compose_target):
        os.remove(docker_compose_target)
        info(f"🗑️ Đã xóa docker-compose PHP của {domain}")

    return {
        "container_id": container_id,
        "site_data": site_data,
        "domain": domain,
    }

def setup_ssl(domain):
    """Cài SSL tự ký"""
    install_selfsigned_ssl(domain)

@log_call
def setup_nginx_vhost(domain):
    """Copy NGINX vhost config"""
    install_dir = env["INSTALL_DIR"]
    nginx_template = os.path.join(
        install_dir, "core", "templates", "nginx-vhost.conf.template")
    nginx_target_dir = os.path.join(env["CONFIG_DIR"], "nginx", "conf.d")
    nginx_target_path = os.path.join(nginx_target_dir, f"{domain}.conf")

    if not os.path.exists(nginx_target_dir):
        os.makedirs(nginx_target_dir, exist_ok=True)

    if os.path.isfile(nginx_template):
        with open(nginx_template, "r") as f:
            content = f.read().replace("${DOMAIN}", domain)
        with open(nginx_target_path, "w") as f:
            f.write(content)
        nginx_restart()


def cleanup_nginx_vhost(domain):
    """Xóa NGINX vhost config"""
    nginx_target_path = os.path.join(
        env["CONFIG_DIR"], "nginx", "conf.d", f"{domain}.conf")
    if os.path.isfile(nginx_target_path):
        os.remove(nginx_target_path)
        info(f"🗑️ Đã xóa file NGINX vhost {domain}")

# =========================
# Danh sách actions
# =========================


def setup_database(domain, php_version):
    """Tạo database và user cho website"""
    setup_database_for_website(domain)


def cleanup_database(domain):
    """Xóa database và user cho website"""
    delete_database(domain)
    delete_database_user(domain)


WEBSITE_SETUP_ACTIONS = [
    (setup_directories, cleanup_directories),
    (setup_php_configs, None),
    (setup_compose_php, cleanup_compose_php),
    (setup_database, cleanup_database),
    (setup_ssl, None),
    (setup_nginx_vhost, cleanup_nginx_vhost),
    (setup_config, cleanup_config),  # Cần để cuối cùng
]

WEBSITE_CLEANUP_ACTIONS = [
    cleanup_nginx_vhost,
    cleanup_compose_php,
    cleanup_database,
    cleanup_config,
    cleanup_directories
]

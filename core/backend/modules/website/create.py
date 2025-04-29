from core.backend.modules.website.website_utils import _is_website_exists
import os
from core.backend.utils.env_utils import env
from core.backend.utils.debug import log_call, info, warn, error, success
from core.backend.objects.config import Config
from core.backend.objects.container import Container


@log_call
def create_website(domain: str, php_version: str):
    config = Config()

    sites_dir = env["SITES_DIR"]
    site_dir = os.path.join(sites_dir, domain)

    if not os.path.isdir(sites_dir):
        os.makedirs(sites_dir, exist_ok=True)
        info(f"📁 Đã tạo thư mục SITES_DIR: {sites_dir}")

    if _is_website_exists(domain):
        warn(f"⚠️ Website {domain} đã tồn tại.")
        return

    try:
        # Tạo thư mục cấu trúc website
        os.makedirs(os.path.join(site_dir, "php"), exist_ok=True)
        os.makedirs(os.path.join(site_dir, "wordpress"), exist_ok=True)
        os.makedirs(os.path.join(site_dir, "logs"), exist_ok=True)
        os.makedirs(os.path.join(site_dir, "backups"), exist_ok=True)
        os.makedirs(os.path.join(site_dir, "ssl"), exist_ok=True)

        for log_file in ["access.log", "error.log", "php_error.log", "php_slow.log"]:
            log_path = os.path.join(site_dir, "logs", log_file)
            open(log_path, "a").close()
            os.chmod(log_path, 0o666)

        # Copy template version nếu có
        template_ver = os.path.join(
            env["INSTALL_DIR"], "core", "templates", ".template_version")
        if os.path.isfile(template_ver):
            os.system(f"cp {template_ver} {site_dir}/.template_version")
            info(f"✅ Copied .template_version to {site_dir}")
        else:
            warn(f"⚠️ Không tìm thấy file template version: {template_ver}")

        # Ghi cấu hình vào config.json
        if config.get("site") is None:
            config.set("site", {}, split_path=False)

        current_sites = config.get("site")
        current_sites[domain] = {
            "domain": domain,
            "php_version": php_version
        }
        logs_dir = os.path.join(site_dir, "logs")
        current_sites[domain]["logs"] = {
            "access": os.path.join(logs_dir, "access.log"),
            "error": os.path.join(logs_dir, "error.log"),
            "php_error": os.path.join(logs_dir, "php_error.log"),
            "php_slow": os.path.join(logs_dir, "php_slow.log")
        }
        config.set("site", current_sites, split_path=False)
        config.save()
        info(f"✅ Đã ghi cấu hình website {domain} vào config.json")

        # Copy php.ini và cấu hình PHP-FPM
        php_ini_template = os.path.join(env["INSTALL_DIR"], "core", "templates", "php.ini.template")
        php_ini_target = os.path.join(site_dir, "php", "php.ini")
        timezone = config.get("core.timezone", "UTC")

        if os.path.isfile(php_ini_template):
            with open(php_ini_template, "r") as f:
                content = f.read().replace("${TIMEZONE}", timezone)
            with open(php_ini_target, "w") as f:
                f.write(content)
            info(f"✅ Đã tạo file php.ini cho {domain} với timezone: {timezone}")
        else:
            warn(f"⚠️ Không tìm thấy file template php.ini: {php_ini_template}")

        from core.backend.modules.website.website_utils import website_calculate_php_fpm_values
        fpm_values = website_calculate_php_fpm_values()
        pm_mode = fpm_values["pm_mode"]
        max_children = fpm_values["max_children"]
        start_servers = fpm_values["start_servers"]
        min_spare_servers = fpm_values["min_spare_servers"]
        max_spare_servers = fpm_values["max_spare_servers"]
        php_fpm_conf_path = os.path.join(site_dir, "php", "php-fpm.conf")
        with open(php_fpm_conf_path, "w") as f:
            f.write(f"""[www]
user = nobody
group = nogroup
listen = 9000
pm = {pm_mode}
pm.max_children = {max_children}
pm.start_servers = {start_servers}
pm.min_spare_servers = {min_spare_servers}
pm.max_spare_servers = {max_spare_servers}
pm.process_idle_timeout = 10s
pm.max_requests = 1000
slowlog=/var/www/logs/php_slow.log
request_slowlog_timeout = 10
request_terminate_timeout = 60
""")
        info(f"✅ Đã tạo file php-fpm.conf với pm_mode = {pm_mode}")

        # Copy docker-compose PHP template
        php_container = f"{domain}-php"
        docker_compose_template = os.path.join(env["INSTALL_DIR"], "core", "templates", "docker-compose.php.yml.template")
        docker_compose_target = os.path.join(site_dir, "docker-compose.php.yml")

        if os.path.isfile(docker_compose_template):
            with open(docker_compose_template, "r") as f:
                content = f.read()
            content = content.replace("${php_container}", php_container)
            content = content.replace("${php_version}", php_version)
            content = content.replace("${PROJECT_NAME}", env["PROJECT_NAME"])
            content = content.replace("${CORE_DIR}", os.path.join(env["INSTALL_DIR"], "core"))
            content = content.replace("${DOCKER_NETWORK}", env["DOCKER_NETWORK"])
            content = content.replace("${domain}", domain)

            with open(docker_compose_target, "w") as f:
                f.write(content)

            info(f"✅ Đã tạo file docker-compose.yml cho {domain}")
        else:
            warn(f"⚠️ Không tìm thấy template docker-compose PHP: {docker_compose_template}")

        # Khởi tạo container PHP cho website
        container = Container(
            name=php_container,
            template_path=docker_compose_template,
            output_path=docker_compose_target,
            env_map={
                "PROJECT_NAME": env["PROJECT_NAME"],
                "CORE_DIR": os.path.join(env["INSTALL_DIR"], "core"),
                "DOCKER_NETWORK": env["DOCKER_NETWORK"],
                "domain": domain,
                "php_container": php_container,
                "php_version": php_version
            }
        )
        container.ensure_ready()

        # Copy NGINX vhost template
        nginx_template = os.path.join(env["INSTALL_DIR"], "core", "templates", "nginx-vhost.conf.template")
        nginx_target_dir = os.path.join(env["CONFIG_DIR"], "nginx", "conf.d")
        nginx_target_path = os.path.join(nginx_target_dir, f"{domain}.conf")

        if not os.path.exists(nginx_target_dir):
            os.makedirs(nginx_target_dir, exist_ok=True)

        if os.path.isfile(nginx_template):
            with open(nginx_template, "r") as f:
                content = f.read().replace("${DOMAIN}", domain)
            with open(nginx_target_path, "w") as f:
                f.write(content)
            info(f"✅ Đã tạo file cấu hình NGINX vhost cho {domain}")
        else:
            warn(f"⚠️ Không tìm thấy template NGINX vhost: {nginx_template}")

        success(f"✅ Website {domain} đã được khởi tạo tại {site_dir}")

    except Exception as e:
        error(f"❌ Lỗi khi tạo website: {e}")
        if os.path.isdir(site_dir):
            os.system(f"rm -rf {site_dir}")
        return

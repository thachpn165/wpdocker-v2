# File: core/backend/bootstraps/wpcli_bootstrap.py

from core.backend.utils.env_utils import env_required, env
from core.backend.utils.debug import info, debug, warn, error, log_call, success
from core.backend.objects.compose import Compose
from core.backend.modules.mysql.utils import get_mysql_root_password

import os


@log_call
def run_wpcli_bootstrap():
    """
    Khởi tạo container WP-CLI để quản lý WordPress qua docker.
    """

    env_required([
        "PROJECT_NAME",
        "WPCLI_CONTAINER_NAME",
        "DOCKER_NETWORK",
        "INSTALL_DIR",
        "SITES_DIR",
        "MYSQL_CONTAINER_NAME",
        "CONFIG_DIR"
    ])

    project_name = env["PROJECT_NAME"]
    wpcli_container = env["WPCLI_CONTAINER_NAME"]
    docker_network = env["DOCKER_NETWORK"]
    install_dir = env["INSTALL_DIR"]
    sites_dir = env["SITES_DIR"]
    mysql_container = env["MYSQL_CONTAINER_NAME"]
    config_dir = env["CONFIG_DIR"]
    templates_dir = os.path.join(install_dir, "core", "templates")

    # Đảm bảo file cấu hình PHP cho WP-CLI tồn tại
    wpcli_ini_target = os.path.join(config_dir, "wpcli-custom.ini")
    wpcli_ini_template = os.path.join(templates_dir, "wpcli-custom.ini")

    if not os.path.exists(wpcli_ini_target):
        if os.path.exists(wpcli_ini_template):
            os.makedirs(config_dir, exist_ok=True)
            with open(wpcli_ini_template, "r") as src, open(wpcli_ini_target, "w") as dst:
                dst.write(src.read())
            info(f"✅ Đã copy wpcli-custom.ini vào {wpcli_ini_target}")
        else:
            error(f"❌ Không tìm thấy template: {wpcli_ini_template}")
            return


    mysql_root_pass = get_mysql_root_password()
    if not mysql_root_pass:
        return

    compose_template = os.path.join(
        install_dir, "core", "templates", "docker-compose.wpcli.yml.template")
    compose_output = os.path.join(
        install_dir, "docker-compose", "docker-compose.wpcli.yml")

    if not os.path.isfile(compose_template):
        error(f"❌ Không tìm thấy file template: {compose_template}")
        return

    compose = Compose(
        name=wpcli_container,
        template_path=compose_template,
        output_path=compose_output,
        env_map={
            "PROJECT_NAME": project_name,
            "WPCLI_CONTAINER_NAME": wpcli_container,
            "DOCKER_NETWORK": docker_network,
            "SITES_DIR": sites_dir,
            "MYSQL_CONTAINER_NAME": mysql_container,
            "MYSQL_ROOT_PASSWORD": mysql_root_pass,
            "CONFIG_DIR": config_dir,
        }
    )

    compose.ensure_ready()
    success(f"✅ Đã khởi tạo container WP-CLI: {wpcli_container}")

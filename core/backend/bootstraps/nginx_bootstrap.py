from core.backend.objects.compose import Compose
from core.backend.objects.container import Container
from core.backend.utils.env_utils import env_required
from core.backend.utils.debug import info, debug
import os

def run_bootstrap():
    info("Khởi tạo hệ thống Webserver NGINX...")

    # Lấy biến cần thiết từ môi trường
    env = env_required([
        "INSTALL_DIR",
        "PROJECT_NAME",
        "NGINX_CONTAINER_NAME",
        "NGINX_IMAGE_NAME",
        "DOCKER_NETWORK",
        "NGINX_CONTAINER_PATH",
        "NGINX_CONTAINER_CONF_PATH"
    ])

    nginx_conf_path = os.path.join(env["INSTALL_DIR"], "core/backend/modules/nginx/nginx.conf")
    nginx_conf_template = os.path.join(env["INSTALL_DIR"], "core/templates/nginx.conf.template")

    # Tạo nginx.conf nếu chưa tồn tại
    if not os.path.exists(nginx_conf_path):
        debug(f"Thiếu file cấu hình NGINX: {nginx_conf_path} → tạo từ template.")

        with open(nginx_conf_template, "r") as f:
            content = f.read()

        content = content.replace("${NGINX_CONTAINER_PATH}", env["NGINX_CONTAINER_PATH"])
        content = content.replace("${NGINX_CONTAINER_CONF_PATH}", env["NGINX_CONTAINER_CONF_PATH"])

        with open(nginx_conf_path, "w") as f:
            f.write(content)

    # Khởi tạo Compose object
    compose = Compose(
        name=env["NGINX_CONTAINER_NAME"],
        template_path=f"{env['INSTALL_DIR']}/core/templates/docker-compose.nginx.yml.template",
        output_path=f"{env['INSTALL_DIR']}/docker-compose/docker-compose.nginx.yml",
        env_map={
            "INSTALL_DIR": env["INSTALL_DIR"],
            "PROJECT_NAME": env["PROJECT_NAME"],
            "NGINX_CONTAINER_NAME": env["NGINX_CONTAINER_NAME"],
            "NGINX_IMAGE_NAME": env["NGINX_IMAGE_NAME"],
            "DOCKER_NETWORK": env["DOCKER_NETWORK"],
            "NGINX_CONTAINER_PATH": env["NGINX_CONTAINER_PATH"],
            "NGINX_CONTAINER_CONF_PATH": env["NGINX_CONTAINER_CONF_PATH"]
        }
    )

    compose.ensure_ready()

    # Khởi tạo Container object để kiểm tra và phân quyền
    container = Container(name=env["NGINX_CONTAINER_NAME"])

    # Danh sách thư mục cần kiểm tra phân quyền
    paths_to_check = [
        env["NGINX_CONTAINER_CONF_PATH"],
        "/var/www"
    ]

    for path in paths_to_check:
        container.exec(["chown", "-R", "www-data:www-data", path], user="root")
        debug(f"Đã chown {path} về www-data:www-data")
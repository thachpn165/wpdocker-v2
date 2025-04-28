from core.backend.objects.container import Container
from core.backend.utils.env_utils import env_required
from core.backend.utils.debug import info, debug

def run_bootstrap():
    info("🚀 Khởi tạo hệ thống Webserver NGINX...")

    # Lấy biến cần thiết từ môi trường
    env = env_required([
        "INSTALL_DIR",
        "PROJECT_NAME",
        "NGINX_CONTAINER_NAME",
        "NGINX_IMAGE_NAME",
        "DOCKER_NETWORK"
    ])

    # Khởi tạo Container object
    container = Container(
        name=env["NGINX_CONTAINER_NAME"],
        template_path=f"{env['INSTALL_DIR']}/core/templates/docker-compose.nginx.yml.template",
        output_path=f"{env['INSTALL_DIR']}/docker-compose/docker-compose.nginx.yml",
        env_map={
            "INSTALL_DIR": env["INSTALL_DIR"],
            "PROJECT_NAME": env["PROJECT_NAME"],
            "NGINX_CONTAINER_NAME": env["NGINX_CONTAINER_NAME"],
            "NGINX_IMAGE_NAME": env["NGINX_IMAGE_NAME"],
            "DOCKER_NETWORK": env["DOCKER_NETWORK"]
        }
    )

    # Kiểm tra đảm bảo đã tồn tại đủ docker-compose file và container
    # Nếu thiếu docker-compose thì tạo mới
    # Nếu container chưa tồn tại thì up
    container.ensure_ready()
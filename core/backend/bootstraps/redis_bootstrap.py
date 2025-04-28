import os
from core.backend.utils.env_utils import env_required, env
from core.backend.utils.debug import log_call, info, debug
from core.backend.objects.container import Container

@log_call
def run_redis_bootstrap():
    info("🚀 Đang khởi tạo Redis container...")

    # Bắt buộc các biến cần có
    env_required([
        "INSTALL_DIR",
        "PROJECT_NAME",
        "REDIS_IMAGE",
        "REDIS_CONTAINER_NAME",
        "DOCKER_NETWORK"
    ])

    # Tạo container object
    container = Container(
        name=env["REDIS_CONTAINER_NAME"],
        template_path=f"{env['INSTALL_DIR']}/core/templates/docker-compose.redis.yml.template",
        output_path=f"{env['INSTALL_DIR']}/docker-compose/docker-compose.redis.yml",
        env_map={
            "PROJECT_NAME": env["PROJECT_NAME"],
            "REDIS_IMAGE": env["REDIS_IMAGE"],
            "REDIS_CONTAINER_NAME": env["REDIS_CONTAINER_NAME"],
            "DOCKER_NETWORK": env["DOCKER_NETWORK"]
        }
    )

    # Khởi động nếu cần
    container.ensure_ready()
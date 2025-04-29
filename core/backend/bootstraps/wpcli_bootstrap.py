# File: core/backend/bootstraps/wpcli_bootstrap.py

from core.backend.utils.env_utils import env_required, env
from core.backend.utils.debug import info, debug, warn, error, log_call, success
from core.backend.objects.compose import Compose
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
        "SITES_DIR"
    ])

    project_name = env["PROJECT_NAME"]
    wpcli_container = env["WPCLI_CONTAINER_NAME"]
    docker_network = env["DOCKER_NETWORK"]
    install_dir = env["INSTALL_DIR"]
    sites_dir = env["SITES_DIR"]

    compose_template = os.path.join(install_dir, "core", "templates", "docker-compose.wpcli.yml.template")
    compose_output = os.path.join(install_dir, "docker-compose", "docker-compose.wpcli.yml")

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
        }
    )

    compose.ensure_ready()
    success(f"✅ Đã khởi tạo container WP-CLI: {wpcli_container}")
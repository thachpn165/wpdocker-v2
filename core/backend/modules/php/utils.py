# File: core/backend/modules/php/utils.py

from core.backend.modules.website.website_utils import get_site_config
from python_on_whales import docker
import questionary
from core.backend.utils.validate import _is_arm
from core.backend.utils.debug import debug
from core.backend.modules.php.init_client import init_php_client

# Get PHP container ID by name
def get_php_container_id_by_name(container_name: str) -> str:
    containers = docker.container.list(
        all=True, filters={"name": container_name})
    if not containers:
        raise ValueError(
            f"Không tìm thấy container PHP với tên {container_name}")
    return containers[0].id

# Get PHP container ID by domain
def get_php_container_id(domain: str) -> str:
    site_config = get_site_config(domain)
    if not site_config or not site_config.php_container_id:
        raise ValueError(f"Không tìm thấy Container ID PHP cho website {domain}")
    return site_config.php_container_id

def get_php_container_name(domain: str) -> str:
    c = init_php_client(domain)
    if not c.exists():
        raise ValueError(f"Không tìm thấy Container PHP cho website {domain}")
    container_name = c.get().name
    if not container_name:
        raise ValueError(f"Không tìm thấy tên Container PHP cho website {domain}")
    return container_name

# Choose PHP version
AVAILABLE_PHP_VERSIONS = [
    "8.0",
    "8.1",
    "8.2",
    "8.3",
]
def php_choose_version():
    choices = []
    is_arm = _is_arm()
    for ver in AVAILABLE_PHP_VERSIONS:
        label = f"{ver} (ARM not supported)" if is_arm and ver == "8.0" else ver
        choices.append({"name": label, "value": ver})

    selected = questionary.select(
        "🔢 Chọn phiên bản PHP:",
        choices=choices
    ).ask()

    debug(f"Phiên bản PHP đã chọn: {selected}")
    return selected
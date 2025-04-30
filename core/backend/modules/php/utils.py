# File: core/backend/modules/php/utils.py

from core.backend.modules.website.website_utils import get_site_config
from python_on_whales import docker


def get_php_container_id_by_name(container_name: str) -> str:
    containers = docker.container.list(
        all=True, filters={"name": container_name})
    if not containers:
        raise ValueError(
            f"Không tìm thấy container PHP với tên {container_name}")
    return containers[0].id


def get_php_container_id(domain: str) -> str:
    site_config = get_site_config(domain)
    if not site_config or not site_config.php_container_id:
        raise ValueError(f"Không tìm thấy Container ID PHP cho website {domain}")
    return site_config.php_container_id

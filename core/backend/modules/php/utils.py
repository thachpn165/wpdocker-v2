# File: core/backend/modules/php/utils.py

from core.backend.objects.config import Config
from python_on_whales import docker


def get_php_container_id_by_name(container_name: str) -> str:
    containers = docker.container.list(
        all=True, filters={"name": container_name})
    if not containers:
        raise ValueError(
            f"Không tìm thấy container PHP với tên {container_name}")
    return containers[0].id


def get_php_container_id(domain: str) -> str:
    config = Config()
    container_id = config.get(f"site.{domain}.php_container_id")
    if not container_id:
        raise ValueError(
            f"Không tìm thấy Container ID PHP cho website {domain}")
    return container_id

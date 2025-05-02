# File: core/backend/modules/php/init_client.py

from core.backend.objects.container import Container
from core.backend.utils.debug import error


def init_php_client(domain: str) -> Container:
    """
    Khởi tạo đối tượng Container cho PHP container của website dựa vào domain.
    Tự động kiểm tra tên container hợp lệ và tồn tại trước khi khởi tạo.
    """
    container_name = f"{domain}-php"
    try:
        php_container = Container(container_name)

        if not php_container.exists():
            error(f"❌ Container PHP không tồn tại với tên: {container_name}")
            raise ValueError(f"Container không tồn tại cho website: {domain}")

        return php_container
    except Exception as e:
        error(f"❌ Không thể khởi tạo Container PHP cho {domain}: {e}")
        raise
    
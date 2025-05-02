# File: core/backend/modules/php/extensions/registry.py

from typing import Dict, Type
from core.backend.abc.php_extension import PHPBaseExtension
from core.backend.modules.php.extensions.ioncube_loader import IoncubeLoaderExtension

# Danh sách tất cả các extension hỗ trợ
EXTENSION_REGISTRY: Dict[str, Type[PHPBaseExtension]] = {
    "ioncube_loader": IoncubeLoaderExtension,
    # thêm extension khác tại đây
}

def get_extension_list() -> Dict[str, str]:
    """Trả về dict {id: title} cho tất cả các extension"""
    return {
        ext_id: cls().get_title()
        for ext_id, cls in EXTENSION_REGISTRY.items()
    }

def get_extension_instance(extension_id: str) -> PHPBaseExtension:
    """Khởi tạo class extension theo ID"""
    if extension_id not in EXTENSION_REGISTRY:
        raise ValueError(f"Extension '{extension_id}' không được hỗ trợ.")
    return EXTENSION_REGISTRY[extension_id]()

from core.backend.modules.php.extensions.registry import (
    get_extension_instance,
    EXTENSION_REGISTRY
)
from core.backend.modules.website.website_utils import get_site_config
from core.backend.utils.debug import info, warn


def install_php_extension(domain: str, extension_id: str):
    """Cài đặt 1 extension cho website và cập nhật config"""
    ext = get_extension_instance(extension_id)
    ext.install(domain)
    ext.update_config(domain)  
    ext.post_install(domain)

def php_restore_enabled_extensions(domain: str):
    """Khôi phục lại toàn bộ extension PHP đã được cài (dựa theo config.json)"""
    site_config = get_site_config(domain)
    if not site_config or not site_config.php:
        warn(f"⚠️ Không tìm thấy cấu hình PHP cho website {domain}")
        return

    extensions = site_config.php.php_installed_extensions or []
    if not extensions:
        info(f"💤 Website {domain} chưa có extension PHP nào được cài.")
        return

    info(f"🔁 Đang khôi phục các extension PHP cho {domain}...")
    for ext_id in extensions:
        try:
            if ext_id not in EXTENSION_REGISTRY:
                warn(f"⚠️ Extension '{ext_id}' không nằm trong danh sách hỗ trợ.")
                continue

            ext = get_extension_instance(ext_id)
            ext.install(domain)
            ext.update_config(domain)  
        except Exception as e:
            warn(f"⚠️ Lỗi khi cài extension '{ext_id}': {e}")

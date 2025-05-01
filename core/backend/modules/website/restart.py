from core.backend.modules.website.website_utils import get_site_config
from core.backend.modules.nginx.nginx import restart as nginx_restart
from core.backend.objects.container import Container
from core.backend.utils.debug import log_call, info, error

@log_call
def restart_website(domain: str):
    site_config = get_site_config(domain)
    if not site_config:
        error(f"❌ Không tìm thấy thông tin cấu hình cho website {domain}.")
        return False

    php_container = Container(f"{domain}-php")
    if php_container.exists():
        info(f"🔁 Đang khởi động lại container PHP: {php_container.name}...")
        php_container.restart()
    else:
        error(f"❌ Container PHP {php_container.name} không tồn tại.")
        return False

    nginx_restart()
    info("✅ Đã khởi động lại NGINX để nạp lại cấu hình.")
    return True
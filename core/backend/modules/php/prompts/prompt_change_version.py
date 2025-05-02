from core.backend.modules.php.change_version import php_change_version
from core.backend.modules.website.website_utils import select_website
from core.backend.utils.debug import log_call, info, error, success, warn, debug
from core.backend.modules.php.utils import php_choose_version

@log_call
def prompt_change_php_version():
    domain = select_website("Chọn website để thay đổi phiên bản PHP:")
    if not domain:
        info("Đã huỷ thao tác thay đổi phiên bản PHP.")
        return

    new_php_version = php_choose_version()
    if not new_php_version:
        info("Đã huỷ thao tác thay đổi phiên bản PHP.")
        return

    try:
        php_change_version(domain, new_php_version)
    except Exception as e:
        error(f"❌ Lỗi khi thay đổi phiên bản PHP cho website {domain}: {e}")
        warn("⚠️ Vui lòng kiểm tra lại cấu hình và thử lại.")
        return

    debug(f"✅ Đã thay đổi phiên bản PHP cho website {domain} thành công.")
    info(f"📦 Phiên bản PHP mới: {new_php_version}")
from questionary import select, text
from core.backend.modules.ssl.check import check_ssl
from core.backend.modules.website.website_utils import select_website
from core.backend.utils.debug import log_call, info, warn, error, debug

@log_call
def prompt_check_ssl():
    """
    Hiển thị danh sách các website đã được tạo và cho phép người dùng chọn một website để kiểm tra SSL.
    """
    domain = select_website("Chọn website cần kiểm tra SSL:")
    if not domain:
        info("Đã huỷ thao tác kiểm tra SSL.")
        return

    try:
        check_ssl(domain)
    except Exception as e:
        error(f"Lỗi khi kiểm tra SSL cho {domain}: {e}")
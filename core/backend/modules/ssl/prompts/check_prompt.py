from questionary import select, text
from core.backend.modules.ssl.check import check_ssl
from core.backend.modules.website.website_utils import website_list
from core.backend.utils.debug import log_call, info, warn, error, debug

@log_call
def prompt_check_ssl():
    """
    Hiển thị danh sách các website đã được tạo và cho phép người dùng chọn một website để kiểm tra SSL.
    """
    websites = website_list()
    debug(f"Websites: {websites}")
    if not websites:
        warn("Không tìm thấy website nào để kiểm tra SSL.")
        return

    domain = select("Chọn website cần kiểm tra SSL:", choices=websites).ask()
    if domain is None:
        info("Đã huỷ thao tác kiểm tra SSL.")
        return

    try:
        check_ssl(domain)
    except Exception as e:
        error(f"Lỗi khi kiểm tra SSL cho {domain}: {e}")
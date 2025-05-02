from questionary import select, text
from core.backend.modules.ssl.edit import edit_ssl
from core.backend.modules.website.website_utils import select_website
from core.backend.utils.debug import log_call, info, warn, error, debug

@log_call
def prompt_edit_ssl():
    """
    Hiển thị danh sách các website đã được tạo và cho phép người dùng chọn một website để kiểm tra SSL.
    """
    domain = select_website("Chọn website cần sửa SSL:")
    if not domain:
        info("Đã huỷ thao tác sửa SSL.")
        return

    try:
        edit_ssl(domain)
    except Exception as e:
        error(f"Lỗi khi sửa SSL cho {domain}: {e}")
# File: core/backend/modules/website/prompts/delete_prompt.py

from questionary import select, confirm
from core.backend.modules.website.website_utils import website_list
from core.backend.modules.website.delete import delete_website
from core.backend.utils.debug import log_call, info, warn, error, debug


@log_call
def prompt_delete_website():
    websites = website_list()
    debug(f"Websites: {websites}")
    if not websites:
        warn("Không tìm thấy website nào để xoá.")
        return

    domain = select("Chọn website cần xoá:", choices=websites).ask()
    if domain is None:
        info("Đã huỷ thao tác xoá.")
        return

    confirm_delete = confirm(
        f"⚠️ Bạn có chắc chắn muốn xoá website '{domain}' không?", default=False).ask()

    if not confirm_delete:
        info("Đã huỷ thao tác xoá.")
        return

    delete_website(domain)
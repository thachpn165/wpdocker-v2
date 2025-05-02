# File: core/backend/modules/website/prompts/delete_prompt.py

from questionary import confirm
from core.backend.modules.website.website_utils import select_website
from core.backend.modules.website.delete import delete_website
from core.backend.utils.debug import log_call, info, warn


@log_call
def prompt_delete_website():
    domain = select_website("Chọn website cần xoá:")
    if not domain:
        info("Đã huỷ thao tác xoá.")
        return

    confirm_delete = confirm(
        f"⚠️ Bạn có chắc chắn muốn xoá website '{domain}' không?", default=False).ask()

    if not confirm_delete:
        info("Đã huỷ thao tác xoá.")
        return

    delete_website(domain)
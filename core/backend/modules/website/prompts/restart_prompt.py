from core.backend.modules.website.website_utils import select_website
from core.backend.modules.website.restart import restart_website
from core.backend.utils.debug import log_call, info, error

@log_call
def prompt_restart_website():
    domain = select_website("🌐 Chọn website cần restart:")
    if not domain:
        error("❌ Bạn chưa chọn website.")
        return
    restart_website(domain)
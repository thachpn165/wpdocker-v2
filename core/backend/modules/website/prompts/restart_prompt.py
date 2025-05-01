from core.backend.modules.website.website_utils import website_list
from core.backend.modules.website.restart import restart_website
from core.backend.utils.debug import log_call, info, error
import questionary

@log_call
def prompt_restart_website():
    domains = website_list()
    if not domains:
        error("⚠️ Không có website nào để khởi động lại.")
        return

    domain = questionary.select("🌐 Chọn website cần restart:", choices=domains).ask()
    if not domain:
        error("❌ Bạn chưa chọn website.")
        return

    restart_website(domain)
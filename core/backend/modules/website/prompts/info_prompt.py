from core.backend.modules.website.website_utils import website_list
from core.backend.utils.debug import log_call, info
from core.backend.modules.website.info import info_website
from questionary import select
from rich.console import Console

console = Console()
@log_call
def prompt_info_website():
    """
    Hiển thị thông tin chi tiết của một website.
    """
    domains = website_list()
    if not domains:
        console.print("[bold red]⚠️ Không có website nào để xem thông tin.")
        return

    domain = select("🌐 Chọn website cần xem thông tin:", choices=domains).ask()
    if not domain:
        console.print("[bold red]❌ Bạn chưa chọn website.")
        return

    info_website(domain)
from core.backend.modules.website.website_utils import select_website
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
    domain = select_website("🌐 Chọn website cần xem thông tin:")
    if not domain:
        console.print("[bold red]❌ Bạn chưa chọn website.")
        return

    info_website(domain)
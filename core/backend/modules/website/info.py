from core.backend.modules.website.website_utils import get_site_config
from core.backend.utils.debug import log_call, error
from core.backend.utils.crypto import decrypt
from rich.console import Console
from rich.table import Table
from rich.text import Text
from core.backend.objects.container import Container

console = Console()

# Các hàm chữ có màu
def label_text(label: str, style: str = "bold green") -> Text:
    return Text(label, style=style)

# Hàm xem thông tin website
@log_call
def info_website(domain: str):
    site_config = get_site_config(domain)
    if not site_config:
        error(f"Không tìm thấy cấu hình cho website {domain}.")
        return

    # Lấy thông tin container name từ container ID
    container_id = site_config.php_container_id or "-"
    container_name = "-"
    if container_id != "-":
        container = Container(container_id)
        info = container.get()
        if info and hasattr(info, "name"):
            container_name = info.name

    table = Table(title=f"📄 Thông tin website: {domain}", header_style="bold cyan")
    table.add_column("Thuộc tính", style="bold", no_wrap=True)
    table.add_column("Giá trị", style="white")

    table.add_row(label_text("Domain"), site_config.domain)
    table.add_row(label_text("PHP Version"), site_config.php_version or "-")
    table.add_row(label_text("Cache"), site_config.cache or "-")
    table.add_row(label_text("PHP Container"), container_name)

    if site_config.logs:
        table.add_row(label_text("Access Log"), site_config.logs.access or "-")
        table.add_row(label_text("Error Log"), site_config.logs.error or "-")
        table.add_row(label_text("PHP Error Log"), site_config.logs.php_error or "-")
        table.add_row(label_text("PHP Slow Log"), site_config.logs.php_slow or "-")

    if site_config.mysql:
        db_pass = decrypt(site_config.mysql.db_pass) if site_config.mysql.db_pass else "-"
        table.add_row(label_text("DB Name"), site_config.mysql.db_name or "-")
        table.add_row(label_text("DB User"), site_config.mysql.db_user or "-")
        table.add_row(label_text("DB Pass"), db_pass)

    console.print(table)

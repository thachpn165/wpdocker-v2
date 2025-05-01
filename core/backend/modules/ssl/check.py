import os
import ssl
from datetime import datetime
from core.backend.modules.website.website_utils import get_site_config
from core.backend.utils.debug import error, log_call
from core.backend.utils.env_utils import env
from rich.console import Console
from rich.table import Table

console = Console()

@log_call
def check_ssl(domain: str):
    site_config = get_site_config(domain)
    if not site_config:
        error(f"Không tìm thấy cấu hình cho website {domain}.")
        return

    cert_path = os.path.join(env["SITES_DIR"], domain, "ssl", "cert.crt")
    if not os.path.isfile(cert_path):
        error(f"Không tìm thấy file chứng chỉ: {cert_path}")
        return

    try:
        cert_dict = ssl._ssl._test_decode_cert(cert_path)

        subject = dict(x[0] for x in cert_dict.get("subject", []))
        issuer = dict(x[0] for x in cert_dict.get("issuer", []))
        not_before = cert_dict.get("notBefore")
        not_after = cert_dict.get("notAfter")

        issued_at = datetime.strptime(not_before, "%b %d %H:%M:%S %Y %Z")
        expired_at = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
        now = datetime.utcnow()

        days_left = (expired_at - now).days
        if days_left >= 0:
            status = f"Đang hoạt động ({days_left} ngày còn lại)"
        else:
            status = f"❌ Đã hết hạn ({-days_left} ngày trước)"

        issuer_str = ", ".join(f"{k}={v}" for (k, v) in issuer.items())

        table = Table(title=f"🔒 Thông tin chứng chỉ SSL cho: {domain}", header_style="bold cyan")
        table.add_column("Thuộc tính", style="bold green")
        table.add_column("Giá trị", style="white")

        table.add_row("Trạng thái", f"[blue]{status}[/]" if days_left >= 0 else f"[bold red]{status}[/]")
        table.add_row("Tên miền (CN)", subject.get("commonName", "-"))
        table.add_row("Tổ chức (O)", subject.get("organizationName", "-"))
        table.add_row("Tổ chức phát hành", issuer.get("organizationName", "-"))
        table.add_row("Ngày ký", issued_at.strftime("%d-%m-%Y"))
        table.add_row("Ngày hết hạn", expired_at.strftime("%d-%m-%Y"))
        table.add_row("Chuỗi phát hành", issuer_str)

        console.print(table)

    except Exception as e:
        error(f"Lỗi khi phân tích chứng chỉ: {e}")

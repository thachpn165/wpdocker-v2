from core.backend.modules.website.website_utils import select_website
from core.backend.utils.debug import log_call, info, warn, error, debug
from core.backend.modules.ssl.install import install_selfsigned_ssl, install_letsencrypt_ssl, install_manual_ssl
from questionary import select, text
import os
from core.backend.utils.env_utils import env

@log_call
def prompt_install_ssl(ssl_type):
    """
    Hiển thị danh sách các website đã được tạo và cho phép người dùng chọn một website để cài đặt SSL.
    """
    domain = select_website("Chọn website cần cài đặt SSL:")
    if not domain:
        info("Đã huỷ thao tác cài đặt SSL.")
        return

    try:
        if ssl_type == "selfsigned":
            install_selfsigned_ssl(domain)
        elif ssl_type == "letsencrypt":
            install_letsencrypt_ssl(domain)
        elif ssl_type == "manual":
            info("\nDán nội dung chứng chỉ SSL (PEM). Gồm cả chuỗi trung gian nếu có:")
            cert_content = text("Paste nội dung CERT:").ask()
            if not cert_content:
                info("Nội dung chứng chỉ không hợp lệ. Đã huỷ thao tác.")
                return

            info("\nDán CA Root (tuỳ chọn). Bạn có thể để trống nếu không cần:")
            ca_root = text("Paste CA Root (nếu có):").ask()

            info("\nDán Private Key tương ứng với chứng chỉ:")
            key_content = text("Paste PRIVATE KEY:").ask()
            if not key_content:
                info("Nội dung Private Key không hợp lệ. Đã huỷ thao tác.")
                return

            # Kết hợp cert + CA root nếu có
            full_cert = cert_content.strip() + ("\n" + ca_root.strip() if ca_root else "")

            site_ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
            os.makedirs(site_ssl_dir, exist_ok=True)

            cert_path = os.path.join(site_ssl_dir, "cert.crt")
            key_path = os.path.join(site_ssl_dir, "priv.key")

            with open(cert_path, "w") as f:
                f.write(full_cert.strip())
            with open(key_path, "w") as f:
                f.write(key_content.strip())

            install_manual_ssl(domain, full_cert.strip(), key_content.strip())
        else:
            error("Loại SSL không hợp lệ.")
            return
    except (KeyboardInterrupt, EOFError):
        info("\nĐã huỷ thao tác nhập SSL.")
        return

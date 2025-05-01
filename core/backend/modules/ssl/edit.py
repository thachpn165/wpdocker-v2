import os
import subprocess
from core.backend.utils.env_utils import env
from core.backend.modules.website.website_utils import get_site_config
from core.backend.utils.debug import error, log_call, info
from core.backend.utils.editor import choose_editor

@log_call
def edit_ssl(domain: str):
    site_config = get_site_config(domain)
    if not site_config:
        error(f"Không tìm thấy cấu hình cho website {domain}.")
        return

    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    cert_path = os.path.join(ssl_dir, "cert.crt")
    key_path = os.path.join(ssl_dir, "priv.key")

    if not os.path.exists(cert_path):
        error(f"Không tìm thấy file cert.crt tại {cert_path}")
        return
    if not os.path.exists(key_path):
        error(f"Không tìm thấy file priv.key tại {key_path}")
        return

    editor = choose_editor()
    if not editor:
        error("Không chọn được trình soạn thảo.")
        return

    info("Đang mở file chứng chỉ và private key để chỉnh sửa...")
    subprocess.call([editor, cert_path])
    subprocess.call([editor, key_path])

# File: core/backend/modules/ssl/install.py

import os
from core.backend.utils.env_utils import env
from core.backend.utils.debug import log_call, info, warn, error, success
from core.backend.utils.validate import _is_valid_domain
from core.backend.modules.nginx.nginx import reload as nginx_reload
from pathlib import Path
import subprocess


@log_call
def install_selfsigned_ssl(domain: str):
    if not _is_valid_domain(domain):
        error(f"❌ Tên miền không hợp lệ: {domain}")
        return False

    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    cert_path = os.path.join(ssl_dir, "cert.crt")
    key_path = os.path.join(ssl_dir, "priv.key")

    os.makedirs(ssl_dir, exist_ok=True)

    cmd = [
        "openssl", "req", "-x509", "-nodes", "-days", "365",
        "-newkey", "rsa:2048",
        "-keyout", key_path,
        "-out", cert_path,
        "-subj", f"/C=VN/ST=HCM/L=HCM/O=WP-Docker/OU=Dev/CN={domain}"
    ]

    try:
        subprocess.run(cmd, check=True)
        success(f"✅ Đã tạo chứng chỉ SSL self-signed cho {domain}")
        nginx_reload()
        return True
    except subprocess.CalledProcessError as e:
        error(f"❌ Lỗi tạo SSL self-signed cho {domain}: {e}")
        return False


@log_call
def install_manual_ssl(domain: str, cert_content: str, key_content: str):
    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    os.makedirs(ssl_dir, exist_ok=True)

    cert_path = os.path.join(ssl_dir, "cert.crt")
    key_path = os.path.join(ssl_dir, "priv.key")

    try:
        with open(cert_path, "w") as f:
            f.write(cert_content.strip())

        with open(key_path, "w") as f:
            f.write(key_content.strip())

        success(f"✅ Đã lưu SSL thủ công cho {domain}")
        nginx_reload()
        return True
    except Exception as e:
        error(f"❌ Không thể ghi SSL thủ công: {e}")
        return False


@log_call
def edit_ssl_cert(domain: str, new_cert: str, new_key: str):
    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")
    cert_path = os.path.join(ssl_dir, "cert.crt")
    key_path = os.path.join(ssl_dir, "priv.key")

    if not os.path.isfile(cert_path) or not os.path.isfile(key_path):
        error(f"❌ Không tìm thấy file SSL hiện tại của {domain}")
        return False

    try:
        with open(cert_path, "w") as f:
            f.write(new_cert.strip())
        with open(key_path, "w") as f:
            f.write(new_key.strip())

        success(f"✅ Đã cập nhật SSL cho {domain}")
        nginx_reload()
        return True
    except Exception as e:
        error(f"❌ Lỗi khi cập nhật SSL: {e}")
        return False
    
    
@log_call
def install_letsencrypt_ssl(domain: str, email: str, staging: bool = False):
    if not _is_valid_domain(domain):
        error(f"❌ Tên miền không hợp lệ: {domain}")
        return False

    if not email or "@" not in email:
        error(f"❌ Email không hợp lệ: {email}")
        return False

    webroot = os.path.join(env["SITES_DIR"], domain, "wordpress")
    certbot_data = os.path.join(env["INSTALL_DIR"], ".certbot")
    ssl_dir = os.path.join(env["SITES_DIR"], domain, "ssl")

    if not os.path.isdir(webroot):
        error(f"❌ Không tìm thấy thư mục webroot: {webroot}")
        return False

    os.makedirs(certbot_data, exist_ok=True)
    os.makedirs(ssl_dir, exist_ok=True)

    certbot_args = [
        "certonly",
        "--webroot", "-w", "/var/www/html",
        "-d", domain,
        "--non-interactive",
        "--agree-tos",
        "-m", email
    ]

    if staging:
        certbot_args.append("--staging")

    try:
        from python_on_whales import docker

        docker.run(
            image="certbot/certbot",
            remove=True,
            volumes=[
                f"{webroot}:/var/www/html",
                f"{certbot_data}:/etc/letsencrypt"
            ],
            command=certbot_args
        )

        cert_path = os.path.join(certbot_data, "live", domain, "fullchain.pem")
        key_path = os.path.join(certbot_data, "live", domain, "privkey.pem")

        if not os.path.isfile(cert_path) or not os.path.isfile(key_path):
            error(f"❌ Không tìm thấy chứng chỉ SSL Let's Encrypt cho {domain}")
            return False

        # Copy cert vào thư mục website
        with open(cert_path, "r") as f:
            cert_content = f.read()
        with open(key_path, "r") as f:
            key_content = f.read()

        with open(os.path.join(ssl_dir, "cert.crt"), "w") as f:
            f.write(cert_content)
        with open(os.path.join(ssl_dir, "priv.key"), "w") as f:
            f.write(key_content)

        success(f"✅ Đã cài đặt SSL Let's Encrypt thành công cho {domain}")
        nginx_reload()
        return True

    except Exception as e:
        error(f"❌ Lỗi khi cài đặt Let's Encrypt SSL cho {domain}: {e}")
        return False
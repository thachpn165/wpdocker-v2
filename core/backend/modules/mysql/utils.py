from core.backend.objects.config import Config
from core.backend.utils.crypto import decrypt
from core.backend.utils.debug import debug, error
from core.backend.modules.website.website_utils import get_site_config
from core.backend.objects.container import Container


def get_mysql_root_password():
    """
    Lấy mật khẩu root MySQL đã giải mã từ config.json
    """
    config = Config()
    encrypted_pass = config.get().get("mysql", {}).get("root_passwd")
    if not encrypted_pass:
        error("❌ Không tìm thấy mysql.root_passwd trong config.")
        return None
    try:
        password = decrypt(encrypted_pass)
        debug(f"🔑 MySQL root password (decrypted): {password}")
        return password
    except Exception as e:
        error(f"❌ Lỗi giải mã mật khẩu MySQL: {e}")
        return None

def get_domain_db_pass(domain):
    """
    Lấy mật khẩu database đã giải mã cho domain cụ thể từ config.json
    """
    site_config = get_site_config(domain)
    if not site_config or not site_config.mysql:
        error(f"❌ Không tìm thấy cấu hình mysql cho domain {domain} trong config.")
        return None

    encrypted_pass = site_config.mysql.db_pass if site_config.mysql else None
    if not encrypted_pass:
        error(f"❌ Không tìm thấy db_pass cho domain {domain} trong cấu hình.")
        return None

    try:
        password = decrypt(encrypted_pass)
        return password
    except Exception as e:
        error(f"Lỗi giải mã mật khẩu database cho domain {domain}: {e}")
        return None


def detect_mysql_client(container: Container) -> str:
    result = container.exec(["which", "mariadb"])
    if result is not None and result.strip() != "":
        return "mariadb"

    result = container.exec(["which", "mysql"])
    if result is not None and result.strip() != "":
        return "mysql"

    raise RuntimeError("❌ Không tìm thấy lệnh mariadb hoặc mysql trong container.")
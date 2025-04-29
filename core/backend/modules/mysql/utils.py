from core.backend.objects.config import Config
from core.backend.utils.crypto import decrypt
from core.backend.utils.debug import debug, error

def get_mysql_root_password():
    """
    Lấy mật khẩu root MySQL đã giải mã từ config.json
    """
    config = Config()
    encrypted_pass = config.get("mysql.root_passwd")
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
    config = Config()
    encrypted_pass = config.get(f"site.{domain}.mysql.db_pass")
    if not encrypted_pass:
        return None
    try:
        password = decrypt(encrypted_pass)
        return password
    except Exception as e:
        error(f"Lỗi giải mã mật khẩu database cho domain {domain}: {e}")
        return None
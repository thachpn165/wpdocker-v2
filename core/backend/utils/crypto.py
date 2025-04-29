import base64
import os
from pathlib import Path
#from core.backend.utils.env_utils import env_required
from core.backend.utils.debug import log_call


# ==============================
@log_call
def get_secret_file_path():
    from core.backend.utils.env_utils import env_required
    env = env_required(["INSTALL_DIR"])
    return os.path.join(env["INSTALL_DIR"], ".secret_key")

@log_call
def get_secret_key():
    secret_file = get_secret_file_path()
    if not os.path.exists(secret_file):
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        with open(secret_file, "w") as f:
            f.write(key)
        print("🔐 Đã tạo mới .secret_key")
    else:
        key = Path(secret_file).read_text().strip()
    return key
@log_call
def encrypt(plain_text):
    key = get_secret_key()
    combined = f"{key}:{plain_text}"
    return base64.b64encode(combined.encode()).decode()
@log_call
def decrypt(encoded_text):
    key = get_secret_key()
    try:
        decoded = base64.b64decode(encoded_text.encode()).decode()
    except Exception as e:
        raise ValueError(f"Lỗi base64 decode: {str(e)}")

    if ":" not in decoded:
        raise ValueError("Định dạng chuỗi giải mã không hợp lệ.")

    try:
        stored_key, plain = decoded.split(":", 1)
    except ValueError:
        raise ValueError("Không thể tách khóa và dữ liệu từ chuỗi giải mã.")

    if stored_key != key:
        raise ValueError("Khóa giải mã không khớp với .secret_key hiện tại.")

    return plain
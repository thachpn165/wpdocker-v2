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
    decoded = base64.b64decode(encoded_text.encode()).decode()
    stored_key, plain = decoded.split(":", 1)
    if stored_key != key:
        raise ValueError("❌ Sai khóa giải mã.")
    return plain
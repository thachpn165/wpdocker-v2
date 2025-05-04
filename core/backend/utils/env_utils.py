import os
import sys

# ==== Tự động load core.env tại lúc import ====
def load_core_env():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    env_file = os.path.join(base_path, "core.env")

    if not os.path.isfile(env_file):
        print(f"Không tìm thấy file cấu hình: {env_file}")
        return {}

    result = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result

# ✅ Biến môi trường toàn cục
env = load_core_env()

# ✅ Hàm bắt buộc kiểm tra env có đủ biến hay không

def env_required(keys):
    result = {}
    missing = []

    for key in keys:
        value = env.get(key)
        if value is None:
            missing.append(key)
        else:
            result[key] = value

    if missing:
        print(f"Thiếu biến môi trường: {', '.join(missing)}")
        sys.exit(1)

    return result

# ✅ Hàm để lấy giá trị của một biến môi trường
def get_env_value(key, default=None):
    """Lấy giá trị của một biến môi trường từ env.
    
    Args:
        key: Tên của biến môi trường
        default: Giá trị mặc định nếu biến không tồn tại
        
    Returns:
        Giá trị của biến môi trường hoặc giá trị mặc định
    """
    return env.get(key, default)
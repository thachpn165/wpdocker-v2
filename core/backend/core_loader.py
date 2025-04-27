# File: core/backend/core_loader.py

import os
import sys
import subprocess

# ====== Danh sách thư viện bắt buộc ======
REQUIRED_MODULES = {
    "questionary": "questionary",
    "rich": "rich",
    "json": "json",
    "platform": "platform",
    "subprocess": "subprocess",
    "os": "os",
    "sys": "sys",
}

# ====== Kiểm tra và cập nhật pip ======
def check_and_update_pip():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError as e:
        print(f"❌ Không thể cập nhật pip: {e}")
        sys.exit(1)
# ====== Cài đặt nếu thiếu module ======
def check_and_install_modules():
    for import_name, pip_name in REQUIRED_MODULES.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"⚠️ Chưa tìm thấy module: {import_name} → tiến hành cài đặt...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])

# ====== Source file core.env vào os.environ ======
def source_core_env():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_file = os.path.join(base_path, "core.env")

    if not os.path.isfile(env_file):
        print(f"❌ Không tìm thấy file cấu hình: {env_file}")
        sys.exit(1)

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()

# ====== Trả toàn bộ biến môi trường đã source dưới dạng dict ======
def load_core_env():
    return dict(os.environ)

# ====== Entry point ======
def init():
    # Nếu không trong virtualenv thì tạo
    if sys.base_prefix == sys.prefix:
        venv_path = "/app/.venv"
        if not os.path.isdir(venv_path):
            print("🐍 Đang tạo virtual environment tại /app/.venv...")
            subprocess.check_call([sys.executable, "-m", "venv", venv_path])
        print("🚀 Đang khởi động lại script trong virtualenv...")
        venv_python = os.path.join(venv_path, "bin", "python")
        os.execv(venv_python, [venv_python] + sys.argv)

    check_and_update_pip()
    check_and_install_modules()
    source_core_env()
    return load_core_env()
# File: core/backend/core_loader.py

from core.backend.utils.crypto import get_secret_key
import os
import sys
import subprocess


# ====== Danh sách thư viện bắt buộc ======
REQUIRED_MODULES = {
    # import_name: pip_name
    
    "questionary": "questionary",
    "rich": "rich",
    "json": "json",
    "platform": "platform",
    "subprocess": "subprocess",
    "os": "os",
    "sys": "sys",
    "base64": "base64",
    "password_generator": "random-password-generator",
    "python_on_whales": "python-on-whales",
    "requests": "requests",
}

# ====== Kiểm tra và cập nhật pip ======


def check_and_update_pip():
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError as e:
        print(f"Không thể cập nhật pip: {e}")
        sys.exit(1)
# ====== Cài đặt nếu thiếu module ======


def check_and_install_modules():
    for import_name, pip_name in REQUIRED_MODULES.items():
        try:
            __import__(import_name)
        except ImportError:
            print(
                f"⚠️ Chưa tìm thấy module: {import_name} → tiến hành cài đặt...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pip_name])

# ====== Source file core.env vào os.environ ======


def source_core_env():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_file = os.path.join(base_path, "core.env")

    if not os.path.isfile(env_file):
        print(f"Không tìm thấy file cấu hình: {env_file}")
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

    # check_and_update_pip()
    check_and_install_modules()
    source_core_env()

    # 🔄 Import debug module sau khi env đã có
    import logging
    from core.backend.utils import debug as debug_module
    from core.backend.utils.debug import debug, enable_exception_hook
    debug_module.logger.setLevel(logging.DEBUG if os.environ.get("DEBUG_MODE", "false").lower() == "true" else logging.INFO)
    #debug_module.enable_exception_hook()
    get_secret_key()
    return load_core_env()

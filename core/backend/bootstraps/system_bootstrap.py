import platform
import subprocess
import questionary
from core.backend.objects.config import Config

def ensure_core_timezone(config: Config):
    if config.get("core.timezone"):
        return

    timezone = questionary.text(
        "🕒 Nhập tên múi giờ (theo TZ database, ví dụ: Asia/Ho_Chi_Minh):"
    ).ask()

    config.set("core.timezone", timezone)
    config.save()

    system_type = platform.system()
    if system_type == "Darwin":
        print("⚠️ Đang dùng macOS, bỏ qua thiết lập múi giờ trên hệ thống.")
        return

    try:
        subprocess.run(["timedatectl", "set-timezone", timezone], check=True)
        print("✅ Đã thiết lập múi giờ hệ thống.")
    except FileNotFoundError:
        print("⚠️ timedatectl không tồn tại trên hệ thống, bỏ qua.")
    except subprocess.CalledProcessError:
        print("❌ Không thể thiết lập múi giờ. Vui lòng kiểm tra quyền hoặc cú pháp.")

def run_system_bootstrap():
    config = Config()
    ensure_core_timezone(config)
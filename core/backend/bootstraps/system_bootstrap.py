import platform
import subprocess
import questionary
from core.backend.objects.config import Config
from core.backend.utils.debug import log_call, info, success, warn, error
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
        warn("Đang dùng macOS, bỏ qua thiết lập múi giờ trên hệ thống.")
        return

    try:
        subprocess.run(["timedatectl", "set-timezone", timezone], check=True)
        success("Đã thiết lập múi giờ hệ thống.")
    except FileNotFoundError:
        warn("timedatectl không tồn tại trên hệ thống, bỏ qua.")
    except subprocess.CalledProcessError:
        error("Không thể thiết lập múi giờ. Vui lòng kiểm tra quyền hoặc cú pháp.")

@log_call
def run_system_bootstrap():
    config = Config()
    ensure_core_timezone(config)
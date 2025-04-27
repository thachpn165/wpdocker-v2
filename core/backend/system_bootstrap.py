import os
import sys
import platform
import subprocess
import questionary

from core.backend.objects.config import Config

def ensure_core_lang(config: Config):
    if config.get("core.lang"):
        return  # Đã có rồi

    lang = questionary.select(
        "🌍 Chọn ngôn ngữ sử dụng:",
        choices=[
            "vi",
            "en"
        ]
    ).ask()

    config.set("core.lang", lang)
    config.save()
    print(f"✅ Đã lưu ngôn ngữ: {lang}")

def ensure_core_channel(config: Config):
    if config.get("core.channel"):
        return  # Đã có rồi

    channel = questionary.select(
        "🚀 Chọn kênh phiên bản (release channel):",
        choices=[
            "stable",
            "beta",
            "dev"
        ]
    ).ask()

    config.set("core.channel", channel)
    config.save()
    print(f"✅ Đã lưu kênh phiên bản: {channel}")

def ensure_core_timezone(config: Config):
    if config.get("core.timezone"):
        return  # Đã có rồi

    timezone = questionary.text(
        "🕒 Nhập tên múi giờ (theo TZ database, ví dụ: Asia/Ho_Chi_Minh):"
    ).ask()

    config.set("core.timezone", timezone)
    config.save()

    # Nếu đang chạy trên Linux thì mới set hệ thống
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

## Run hệ thống bootstrap
def run_system_bootstrap():
    config = Config()  # Mặc định load từ /app/config/config.json
    ensure_core_lang(config)
    ensure_core_channel(config)
    ensure_core_timezone(config)
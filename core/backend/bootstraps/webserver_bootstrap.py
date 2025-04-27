import questionary
from core.backend.objects.config import Config

def run_webserver_bootstrap():
    config = Config()

    if config.get("core.webserver"):
        return  # Đã có rồi

    webserver = questionary.select(
        "🖥️ Chọn Webserver sử dụng:",
        choices=["nginx"],  # Có thể mở rộng sau
    ).ask()

    config.set("core.webserver", webserver)
    config.save()
    print(f"✅ Đã lưu Webserver: {webserver}")
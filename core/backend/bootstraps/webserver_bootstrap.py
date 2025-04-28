import questionary
from core.backend.objects.config import Config
import importlib
from core.backend.utils.debug import debug, info, warn, error, log_call


@log_call
def run_webserver_bootstrap():
    config = Config()
    webserver = config.get("core.webserver")

    available_webservers = {
        "nginx": {
            "label": "NGINX (OpenResty)",
            "module": "core.backend.bootstraps.nginx_bootstrap"
        },
        # "caddy": ...
    }

    # Nếu chưa có thì hỏi chọn và lưu lại
    if not webserver:
        label_to_key = {v["label"]: k for k, v in available_webservers.items()}
        webserver_label = questionary.select(
            "🖥️ Chọn Webserver sử dụng:",
            choices=list(label_to_key.keys())
        ).ask()
        webserver = label_to_key[webserver_label]
        config.set("core.webserver", webserver)
        config.save()
        print(f"✅ Đã lưu Webserver: {webserver}")

    # Luôn khởi tạo webserver nếu đã có tên
    if webserver in available_webservers:
        mod = importlib.import_module(
            available_webservers[webserver]["module"])
        mod.run_bootstrap()
    else:
        error(
            f"❌ Webserver `{webserver}` không nằm trong danh sách được hỗ trợ.")

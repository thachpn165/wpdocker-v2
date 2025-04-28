import importlib
from core.backend.objects.config import Config

def get_current_webserver():
    config = Config()
    webserver = config.get("core.webserver")
    if not webserver:
        raise ValueError("❌ Chưa thiết lập webserver.")
    return webserver

def get_webserver_module():
    webserver = get_current_webserver()
    return importlib.import_module(f"core.backend.modules.{webserver}")

def reload_webserver():
    mod = get_webserver_module()
    if hasattr(mod, "reload"):
        mod.reload()

def apply_webserver_config():
    mod = get_webserver_module()
    if hasattr(mod, "apply_config"):
        mod.apply_config()
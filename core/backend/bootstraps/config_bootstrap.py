import questionary
from core.backend.objects.config import Config

def ensure_core_lang(config: Config):
    if config.get("core.lang"):
        return

    lang = questionary.select(
        "🌍 Chọn ngôn ngữ sử dụng:",
        choices=["vi", "en"]
    ).ask()

    config.set("core.lang", lang)
    config.save()
    print(f"✅ Đã lưu ngôn ngữ: {lang}")

def ensure_core_channel(config: Config):
    if config.get("core.channel"):
        return

    channel = questionary.select(
        "🚀 Chọn kênh phiên bản (release channel):",
        choices=["stable", "beta", "dev"]
    ).ask()

    config.set("core.channel", channel)
    config.save()
    print(f"✅ Đã lưu kênh phiên bản: {channel}")

def run_config_bootstrap():
    config = Config()
    ensure_core_lang(config)
    ensure_core_channel(config)
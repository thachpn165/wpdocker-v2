import questionary
import jsons
from jsons.exceptions import DeserializationError
from core.backend.models.config import CoreConfig
from core.backend.objects.config import Config
from core.backend.utils.debug import log_call, debug, info, success


@log_call
def run_config_bootstrap():
    config = Config()
    full_config = config.get()
    raw_core = full_config.get("core", {})

    try:
        # ✅ Nếu core config đã hợp lệ, không làm gì cả
        core_config = jsons.load(raw_core, CoreConfig)
        debug("Core config đã tồn tại, bỏ qua việc khởi tạo.")
        return
    except DeserializationError:
        info("⚙️ Đang khởi tạo cấu hình hệ thống...")

    # 👉 Hỏi người dùng các thông tin bắt buộc
    lang = questionary.select(
        "🌍 Chọn ngôn ngữ sử dụng:",
        choices=["vi", "en"]
    ).ask()

    channel = questionary.select(
        "🚀 Chọn kênh phiên bản (release channel):",
        choices=["stable", "beta", "dev"]
    ).ask()

    timezone = questionary.text(
        "⏰ Nhập múi giờ hệ thống (VD: Asia/Ho_Chi_Minh):",
        default="Asia/Ho_Chi_Minh"
    ).ask()

    webserver = questionary.select(
        "🕸️ Chọn webserver:",
        choices=["nginx", "apache"]
    ).ask()

    mysql_version = questionary.select(
        "🐬 Chọn phiên bản MySQL:",
        choices=["10.6", "10.11"]
    ).ask()

    # 👉 Ghi lại cấu hình
    core_config = CoreConfig(
        lang=lang,
        channel=channel,
        timezone=timezone,
        webserver=webserver,
        mysql_version=mysql_version
    )

    config.update_key("core", jsons.dump(core_config))
    config.save()

    success("✅ Cấu hình core đã được khởi tạo thành công!")
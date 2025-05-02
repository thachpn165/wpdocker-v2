# File: core/backend/modules/mysql/edit_config.py

import os
from core.backend.utils.env_utils import env_required
from core.backend.utils.editor import choose_editor
from core.backend.utils.debug import info, error, log_call
from core.backend.objects.container import Container

env = env_required(["MYSQL_CONFIG_FILE", "MYSQL_CONTAINER_NAME"])

@log_call
def edit_mysql_config():
    config_path = env["MYSQL_CONFIG_FILE"]

    if not os.path.isfile(config_path):
        error(f"❌ Không tìm thấy tập tin cấu hình MySQL: {config_path}")
        return

    editor = choose_editor()
    if not editor:
        error("❌ Không có trình soạn thảo nào được chọn.")
        return

    os.system(f"{editor} {config_path}")

    container = Container(env["MYSQL_CONTAINER_NAME"])
    container.restart()
    info("🔁 Đã khởi động lại container MySQL để áp dụng cấu hình.")
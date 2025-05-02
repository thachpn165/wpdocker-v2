# File: core/backend/modules/php/edit_ini.py

import os
from core.backend.utils.env_utils import env
from core.backend.utils.debug import error, info
from core.backend.utils.editor import choose_editor
from core.backend.modules.php.init_client import init_php_client


def edit_php_ini(domain: str):
    """
    Cho phép người dùng chỉnh sửa file php.ini cho website, sau đó restart container PHP.
    """
    try:
        php_ini_path = os.path.join(env["SITES_DIR"], domain, "php", "php.ini")
        if not os.path.isfile(php_ini_path):
            error(f"❌ Không tìm thấy file php.ini cho website {domain} tại {php_ini_path}")
            return

        editor = choose_editor()
        if not editor:
            error("❌ Không có trình soạn thảo nào được chọn.")
            return

        os.system(f"{editor} {php_ini_path}")

        container = init_php_client(domain)
        container.restart()
        info(f"✅ Đã restart container PHP sau khi chỉnh sửa php.ini cho {domain}.")

    except Exception as e:
        error(f"❌ Lỗi khi chỉnh sửa php.ini cho website {domain}: {e}")


def edit_php_fpm_pool(domain: str):
    """
    Cho phép người dùng chỉnh sửa file php-fpm.conf cho website, sau đó restart container PHP.
    """
    try:
        fpm_conf_path = os.path.join(env["SITES_DIR"], domain, "php", "php-fpm.conf")
        if not os.path.isfile(fpm_conf_path):
            error(f"❌ Không tìm thấy file php-fpm.conf cho website {domain} tại {fpm_conf_path}")
            return

        editor = choose_editor()
        if not editor:
            error("❌ Không có trình soạn thảo nào được chọn.")
            return

        os.system(f"{editor} {fpm_conf_path}")

        container = init_php_client(domain)
        container.restart()
        info(f"✅ Đã restart container PHP sau khi chỉnh sửa php-fpm.conf cho {domain}.")

    except Exception as e:
        error(f"❌ Lỗi khi chỉnh sửa php-fpm.conf cho website {domain}: {e}")

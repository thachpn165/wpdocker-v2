# File: core/backend/modules/php/prompts/prompt_edit_config.py

from core.backend.modules.website.website_utils import select_website
from core.backend.modules.php.edit_config import edit_php_ini, edit_php_fpm_pool
from questionary import select
from core.backend.utils.debug import log_call, info

@log_call
def prompt_edit_config():
    domain = select_website("Chọn website cần chỉnh sửa cấu hình PHP:")
    if not domain:
        info("Đã huỷ thao tác chỉnh sửa cấu hình PHP.")
        return

    choice = select(
        "Chọn cấu hình PHP cần chỉnh sửa:",
        choices=[
            {"name": "📄 php.ini", "value": "ini"},
            {"name": "⚙️ php-fpm.conf", "value": "fpm"},
        ]
    ).ask()

    if choice == "ini":
        edit_php_ini(domain)
    elif choice == "fpm":
        edit_php_fpm_pool(domain)
    else:
        info("Đã huỷ thao tác.")

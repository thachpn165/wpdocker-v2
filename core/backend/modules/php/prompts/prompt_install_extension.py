# File: core/backend/modules/php/prompts/prompt_install_extension.py

from core.backend.modules.website.website_utils import select_website
from core.backend.modules.php.extensions.install_extension import install_php_extension
from core.backend.modules.php.extensions.registry import get_extension_list
from questionary import select
from core.backend.utils.debug import log_call, info
from questionary import Choice

@log_call
def prompt_install_php_extension():
    domain = select_website("Chọn website để cài extension PHP:")
    if not domain:
        info("Đã huỷ thao tác.")
        return

    extension_choices = get_extension_list()
    if not extension_choices:
        info("Hiện chưa có extension PHP nào được hỗ trợ.")
        return

    ext_id = select(
        "Chọn extension cần cài:",
        choices=[Choice(title, value=ext_id) for ext_id, title in extension_choices.items()] 
    ).ask()

    if not ext_id:
        info("Đã huỷ thao tác.")
        return

    install_php_extension(domain, ext_id)

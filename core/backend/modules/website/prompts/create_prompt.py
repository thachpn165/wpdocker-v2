from questionary import text, select
from core.backend.modules.website.create import create_website
from core.backend.utils.debug import log_call, info, warn, error, success, debug
from core.backend.utils.validate import _is_valid_domain

def prompt_create_website():
    try:
        domain = ""
        while not domain:
            domain = text("Nhập tên domain website:").ask()
            if domain is None:
                print("Đã huỷ thao tác.")
                return
            if not domain:
                error("Domain không được để trống.")
                domain = ""
                continue
            if not _is_valid_domain(domain):
                error("Tên miền không hợp lệ. Vui lòng nhập đúng định dạng (ví dụ: example.com)")
                domain = ""
                continue
        debug(f"Domain: {domain}")

        php_version = ""
        while not php_version:
            php_version = select(
                "🧩 Chọn phiên bản PHP:",
                choices=["8.0", "8.1", "8.2", "8.3"],
                default="8.2"
            ).ask()
            if php_version is None:
                print("Đã huỷ thao tác.")
                return

        create_website(domain, php_version)

    except (KeyboardInterrupt, EOFError):
        print("\nĐã huỷ thao tác.")
        return
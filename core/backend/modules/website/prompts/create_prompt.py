from questionary import text, select, confirm, password
from core.backend.modules.website.create import create_website
from core.backend.modules.wordpress.install import install_wordpress
from core.backend.utils.debug import log_call, info, warn, error, success, debug
from core.backend.utils.validate import _is_valid_domain
import random
import string
from core.backend.modules.php.utils import php_choose_version

@log_call
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

        php_version = php_choose_version()
        info(f"Phiên bản PHP đã chọn: {php_version}")
        create_website(domain, php_version)

        # ==== Hỏi thông tin cài đặt WordPress ====
        auto_generate = confirm("🔐 Tạo tài khoản WordPress ngẫu nhiên?").ask()
        if auto_generate:
            admin_user = "admin" + ''.join(random.choices(string.ascii_lowercase, k=4))
            admin_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        else:
            admin_user = text("👤 Nhập tên đăng nhập WordPress:").ask()
            
            while True:
                admin_pass = password("🔑 Nhập mật khẩu WordPress:").ask()
                confirm_pass = password("🔁 Nhập lại mật khẩu để xác nhận:").ask()
                if admin_pass != confirm_pass:
                    error("❌ Mật khẩu không khớp. Vui lòng thử lại.")
                elif not admin_pass:
                    error("❌ Mật khẩu không được để trống.")
                else:
                    break

        default_email = f"contact@{domain}"
        admin_email = text("📧 Nhập email quản trị:", default=default_email).ask()

        site_title_guess = domain.split(".")[0].capitalize()
        site_title = text("📛 Nhập tiêu đề website:", default=site_title_guess).ask()

        site_url = f"https://{domain}"

        install_wordpress(
            domain=domain,
            site_url=site_url,
            title=site_title,
            admin_user=admin_user,
            admin_pass=admin_pass,
            admin_email=admin_email
        )

    except (KeyboardInterrupt, EOFError):
        print("\nĐã huỷ thao tác.")
        return
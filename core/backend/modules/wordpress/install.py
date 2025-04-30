# File: core/backend/modules/wordpress/install.py

from core.backend.utils.debug import debug, info, error, success, log_call
from core.backend.modules.wordpress import install_actions as actions


@log_call
def install_wordpress(domain, site_url, title, admin_user, admin_pass, admin_email):
    debug(f"▶️ Bắt đầu cài đặt WordPress cho {domain}")

    # Theo dõi trạng thái để rollback nếu lỗi
    steps_done = []

    if not actions.wordpress_check_containers(domain):
        return False

    if not actions.wordpress_download_core(domain):
        return False
    steps_done.append("wordpress_download_core")

    if not actions.wordpress_generate_config(domain):
        actions.wordpress_delete_core(domain)
        return False
    steps_done.append("wordpress_generate_config")

    if not actions.wordpress_configure_db(domain):
        actions.wordpress_delete_config(domain)
        actions.wordpress_delete_core(domain)
        return False
    steps_done.append("wordpress_configure_db")

    if not actions.wordpress_check_database(domain):
        actions.wordpress_delete_config(domain)
        actions.wordpress_delete_core(domain)
        return False
    steps_done.append("wordpress_check_database")

    if not actions.wordpress_core_install(domain, site_url, title, admin_user, admin_pass, admin_email):
        actions.wordpress_uninstall(domain)
        return False
    steps_done.append("wordpress_core_install")

    if not actions.wordpress_fix_permissions(domain):
        error("⚠️ Cảnh báo: Không thể phân quyền, nhưng cài đặt vẫn tiếp tục.")

    if not actions.wordpress_verify_installation(domain):
        error(f"❌ Xác minh cài đặt WordPress thất bại. Thực hiện rollback...")
        actions.wordpress_uninstall(domain)
        return False

    if not actions.wordpress_save_post_install_config(domain):
        error("❌ Lưu cấu hình sau cài đặt thất bại. Thực hiện rollback...")
        actions.wordpress_delete_post_install_config(domain)
        return False
    
    
    # ✅ Thành công
    success(f"🎉 Website WordPress {domain} đã được cài đặt thành công!")
    info(f"🔑 Thông tin đăng nhập:")
    info(f"🌐 URL: {site_url}/wp-admin")
    info(f"👤 Admin User: {admin_user}")
    info(f"🔒 Admin Password: {admin_pass}")

    # Ghi cấu hình vào config.json
    actions.wordpress_save_post_install_config(domain)
    return True
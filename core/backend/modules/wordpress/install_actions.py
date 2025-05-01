from core.backend.utils.env_utils import env
from core.backend.utils.debug import debug, info, warn, error, success, log_call
from core.backend.objects.container import Container
from core.backend.modules.website.website_utils import ensure_www_data_ownership, get_site_config, set_site_config, delete_site_config
from core.backend.modules.mysql.utils import get_domain_db_pass
from core.backend.modules.mysql.utils import detect_mysql_client
from core.backend.models.config import SiteConfig
from core.backend.modules.website.website_utils import get_site_config, set_site_config, delete_site_config

# Danh sách các key cần lưu vào config.json sau khi cài đặt WordPress
# Chúng ta có thể thêm các key khác vào đây nếu cần thiết
CONFIG_KEYS_AFTER_INSTALL = {
    "cache": "no-cache",
    # có thể thêm các key khác sau như:
    # "installed": True,
    # "installed_at": "2025-04-30T19:30:00Z"
}


@log_call
def wordpress_check_containers(domain):
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    if not wpcli.running():
        error(f"❌ Container WP-CLI ({wpcli.name}) không hoạt động.")
        return False

    php = Container(f"{domain}-php")
    if not php.running():
        error(f"❌ Container PHP {php.name} không chạy.")
        return False

    mysql = Container(env["MYSQL_CONTAINER_NAME"])
    if not mysql.running():
        error(f"❌ Container MySQL {mysql.name} không chạy.")
        return False

    return True


@log_call
def wordpress_download_core(domain):
    import os

    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    sites_dir = env["SITES_DIR"]
    wordpress_path = os.path.join(sites_dir, domain, "wordpress")

    # Kiểm tra thư mục trên host có rỗng không
    is_empty = not os.path.exists(wordpress_path) or not os.listdir(wordpress_path)

    if is_empty:
        debug(f"📥 Tải WordPress vào {wordpress_path}...")
        wpcli.exec(["wp", "core", "download"], workdir=f"/var/www/html/{domain}/wordpress")
    else:
        warn(f"📂 WordPress đã được cài đặt tại {wordpress_path}. Bỏ qua bước tải xuống.")

    return True


@log_call
def wordpress_delete_core(domain):
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"
    wpcli.exec(["rm", "-rf", wordpress_path])
    warn(f"🧹 Đã xóa mã nguồn WordPress tại {wordpress_path}.")


@log_call
def wordpress_generate_config(domain):
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"
    wpcli.exec(["cp", "wp-config-sample.php", "wp-config.php"], workdir=wordpress_path)
    return True


@log_call
def wordpress_delete_config(domain):
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress/wp-config.php"
    wpcli.exec(["rm", "-f", wordpress_path])
    warn(f"🗑️ Đã xóa wp-config.php tại {wordpress_path}.")


@log_call
def wordpress_configure_db(domain):
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"
    site_config = get_site_config(domain)
    db_info = site_config.mysql if site_config and site_config.mysql else None
    if not db_info:
        error("❌ Thiếu thông tin DB trong config.")
        return False
    db_name = getattr(db_info, "db_name", None)
    db_user = getattr(db_info, "db_user", None)
    db_pass = get_domain_db_pass(domain)
    db_host = env["MYSQL_CONTAINER_NAME"]

    if not all([db_name, db_user, db_pass]):
        error("❌ Thiếu thông tin DB trong config.")
        return False

    replacements = {
        "database_name_here": db_name,
        "username_here": db_user,
        "password_here": db_pass,
        "localhost": db_host,
    }
    for search, replace in replacements.items():
        wpcli.exec(["sed", "-i", f"s/{search}/{replace}/g", "wp-config.php"], workdir=wordpress_path)

    return True


@log_call
def wordpress_check_database(domain):
    site_config = get_site_config(domain)
    db_info = site_config.mysql if site_config and site_config.mysql else None
    if not db_info:
        error("❌ Thiếu thông tin DB trong config.")
        return False
    db_name = getattr(db_info, "db_name", None)
    db_user = getattr(db_info, "db_user", None)
    db_pass = get_domain_db_pass(domain)

    if not all([db_name, db_user, db_pass]):
        error("❌ Thiếu thông tin DB trong config.")
        return False

    mysql = Container(env["MYSQL_CONTAINER_NAME"])
    client_cmd = detect_mysql_client(mysql)
    check_cmd = [client_cmd, "-u", db_user, f"-p{db_pass}", "-e", f"USE {db_name};"]
    if mysql.exec(check_cmd) is None:
        error("❌ Kết nối đến database thất bại.")
        return False
    return True


@log_call
def wordpress_core_install(domain, site_url, title, admin_user, admin_pass, admin_email):
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"
    wpcli.exec([
        "wp", "core", "install",
        f"--url={site_url}",
        f"--title={title}",
        f"--admin_user={admin_user}",
        f"--admin_password={admin_pass}",
        f"--admin_email={admin_email}",
        "--skip-email",
    ], workdir=wordpress_path)
    return True


@log_call
def wordpress_uninstall(domain):
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"
    wpcli.exec(["wp", "db", "drop", "--yes"], workdir=wordpress_path)
    wpcli.exec(["rm", "-rf", wordpress_path])
    warn(f"🧨 Đã gỡ toàn bộ WordPress tại {wordpress_path}.")


@log_call
def wordpress_fix_permissions(domain):
    php = Container(f"{domain}-php")
    ensure_www_data_ownership(php.name, "/var/www/html/")
    return True


@log_call
def wordpress_verify_installation(domain):
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"
    result = wpcli.exec(["wp", "core", "is-installed"], workdir=wordpress_path)
    return result is not None

@log_call
def wordpress_save_post_install_config(domain):
    """
    Lưu các key cấu hình sau khi cài đặt WordPress (dùng chung CONFIG_KEYS_AFTER_INSTALL)
    """
    site_config = get_site_config(domain)
    if not site_config:
        error(f"❌ Không tìm thấy cấu hình site {domain} để cập nhật.")
        return False

    for subkey, value in CONFIG_KEYS_AFTER_INSTALL.items():
        setattr(site_config, subkey, value)
        debug(f"📝 Đã gán site_config.{subkey} = {value}")

    set_site_config(domain, site_config)
    return True


@log_call
def wordpress_delete_post_install_config(domain):
    """
    Xóa các key cấu hình được tạo sau khi cài đặt WordPress
    """
    for subkey in CONFIG_KEYS_AFTER_INSTALL.keys():
        deleted = delete_site_config(domain, subkey=subkey)
        if deleted:
            debug(f"🗑️ Đã xóa config site.{domain}.{subkey}")
        else:
            warn(f"⚠️ Không tìm thấy site.{domain}.{subkey} để xóa")
    return True
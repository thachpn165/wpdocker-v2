from core.backend.utils.env_utils import env
from core.backend.utils.debug import debug, info, warn, error, success, log_call
from core.backend.objects.container import Container
from core.backend.modules.website.website_utils import ensure_www_data_ownership, get_site_config, set_site_config, delete_site_config
from core.backend.modules.mysql.utils import get_domain_db_pass
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
    wpcli = Container(env["WPCLI_CONTAINER_NAME"])
    wordpress_path = f"/var/www/html/{domain}/wordpress"

    # Kiểm tra xem WordPress đã được cài đặt chưa
    result = wpcli.exec(["wp", "core", "is-installed"], workdir=wordpress_path)

    if result is None:  # Nếu WordPress chưa được cài đặt
        debug(f"📥 Tải WordPress vào {wordpress_path}...")
        wpcli.exec(["wp", "core", "download"], workdir=wordpress_path)
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
    check_cmd = ["mysql", "-u", db_user, f"-p{db_pass}", "-e", f"USE {db_name};"]
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
    Lưu cấu hình sau khi cài đặt WordPress vào config.json,
    bao gồm key site.<domain>.cache = "no-cache"
    """
    config = Config()
    key_path = f"site.{domain}.cache"
    config.set(key_path, "no-cache", split_path=True)
    debug(f"📝 Đã lưu config site.{domain}.cache = 'no-cache'")
    return True


@log_call
def wordpress_save_post_install_config(domain):
    """
    Lưu các key cấu hình sau khi cài đặt WordPress (dùng chung CONFIG_KEYS_AFTER_INSTALL)
    """
    for subkey, value in CONFIG_KEYS_AFTER_INSTALL.items():
        set_site_config(domain, subkey, value)
        debug(f"📝 Đã lưu config site.{domain}.{subkey} = {value}")
    return True


@log_call
def wordpress_delete_post_install_config(domain):
    """
    Xóa các key cấu hình được tạo sau khi cài đặt WordPress
    """
    for subkey in CONFIG_KEYS_AFTER_INSTALL.keys():
        delete_site_config(domain, subkey)
        debug(f"🗑️ Đã xóa config site.{domain}.{subkey}")
    return True
from core.backend.objects.config import Config
from core.backend.utils.crypto import encrypt
from core.backend.utils.debug import log_call, info, warn, error, debug, success 
from core.backend.modules.mysql.utils import get_mysql_root_password, detect_mysql_client
from core.backend.utils.env_utils import env
from core.backend.models.config import SiteMySQL
from core.backend.modules.website.website_utils import get_site_config, set_site_config
import subprocess
import random
import string
from core.backend.modules.docker.container import Container

mysql_container = Container(name=env["MYSQL_CONTAINER_NAME"])
mysql_client = detect_mysql_client(mysql_container)

@log_call
def create_database(domain):
    db_name = f"{domain.replace('.', '_')}_wpdb"
    mysql_root_pass = get_mysql_root_password()
    if not mysql_root_pass:
        error("❌ Không lấy được mật khẩu root MySQL.")
        return None
    try:
        cmd = [
            "docker", "exec", "-i", env["MYSQL_CONTAINER_NAME"],
            mysql_client, "-uroot", f"-p{mysql_root_pass}",
            "-e", f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        ]
        subprocess.run(cmd, check=True)
        info(f"✅ Đã tạo database: {db_name}")
        return db_name
    except Exception as e:
        error(f"❌ Lỗi khi tạo database: {e}")
        return None

@log_call
def create_database_user(domain):
    db_user = f"{domain.replace('.', '_')}_wpuser"
    db_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    mysql_root_pass = get_mysql_root_password()
    if not mysql_root_pass:
        error("❌ Không lấy được mật khẩu root MySQL.")
        return None, None
    try:
        cmd_create_user = [
            "docker", "exec", "-i", env["MYSQL_CONTAINER_NAME"],
            mysql_client, "-uroot", f"-p{mysql_root_pass}",
            "-e", f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_pass}';"
        ]
        subprocess.run(cmd_create_user, check=True)
        info(f"✅ Đã tạo user: {db_user}")
        return db_user, db_pass
    except Exception as e:
        error(f"❌ Lỗi khi tạo database user: {e}")
        return None, None

@log_call
def grant_privileges(db_name, db_user):
    mysql_root_pass = get_mysql_root_password()
    if not mysql_root_pass:
        error("❌ Không lấy được mật khẩu root MySQL.")
        return False
    try:
        cmd_grant = [
            "docker", "exec", "-i", env["MYSQL_CONTAINER_NAME"],
            mysql_client, "-uroot", f"-p{mysql_root_pass}",
            "-e", f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user}'@'%'; FLUSH PRIVILEGES;"
        ]
        subprocess.run(cmd_grant, check=True)
        info(f"✅ Đã gán quyền cho user {db_user} trên database {db_name}")
        return True
    except Exception as e:
        error(f"❌ Lỗi khi gán quyền database: {e}")
        return False

@log_call
def setup_database_for_website(domain):
    db_name = create_database(domain)
    if not db_name:
        return False
    db_user, db_pass = create_database_user(domain)
    if not db_user or not db_pass:
        return False
    if not grant_privileges(db_name, db_user):
        return False

    # Cập nhật vào config đúng block
    config = Config()
    site_config = get_site_config(domain)
    if not site_config:
        error(f"❌ Không tìm thấy cấu hình website {domain} để cập nhật MySQL.")
        return False

    site_config.mysql = SiteMySQL(
        db_name=db_name,
        db_user=db_user,
        db_pass=encrypt(db_pass)
    )
    set_site_config(domain, site_config)
    success(f"✅ Đã thiết lập database cho website {domain}")
    return True

@log_call
def delete_database(domain):
    db_name = f"{domain.replace('.', '_')}_wpdb"
    mysql_root_pass = get_mysql_root_password()
    if not mysql_root_pass:
        error("❌ Không lấy được mật khẩu root MySQL.")
        return False
    try:
        cmd = [
            "docker", "exec", "-i", env["MYSQL_CONTAINER_NAME"],
            mysql_client, "-uroot", f"-p{mysql_root_pass}",
            "-e", f"DROP DATABASE IF EXISTS `{db_name}`;"
        ]
        subprocess.run(cmd, check=True)
        info(f"🗑️ Đã xóa database: {db_name}")
        return True
    except Exception as e:
        error(f"❌ Lỗi khi xóa database {db_name}: {e}")
        return False

@log_call
def delete_database_user(domain):
    db_user = f"{domain.replace('.', '_')}_wpuser"
    mysql_root_pass = get_mysql_root_password()
    if not mysql_root_pass:
        error("❌ Không lấy được mật khẩu root MySQL.")
        return False
    try:
        cmd = [
            "docker", "exec", "-i", env["MYSQL_CONTAINER_NAME"],
            mysql_client, "-uroot", f"-p{mysql_root_pass}",
            "-e", f"DROP USER IF EXISTS '{db_user}'@'%'; FLUSH PRIVILEGES;"
        ]
        subprocess.run(cmd, check=True)
        info(f"🗑️ Đã xóa user: {db_user}")
        return True
    except Exception as e:
        error(f"❌ Lỗi khi xóa user {db_user}: {e}")
        return False
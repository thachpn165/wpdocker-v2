from datetime import datetime
import os
from core.backend.utils.debug import log_call, info, error
from core.backend.modules.mysql.mysql_exec import (
    run_mysql_dump,
    run_mysql_import,
    run_mysql_command,
)
from core.backend.modules.website.website_utils import get_site_config
from core.backend.utils.env_utils import env_required, env
from core.backend.objects.container import Container


env_required(["MYSQL_CONTAINER_NAME"])
mysql_container = Container(env["MYSQL_CONTAINER_NAME"])

@log_call
def export_database(domain: str, target_folder: str):
    site_config = get_site_config(domain)
    if not site_config or not site_config.mysql:
        error(f"❌ Không tìm thấy cấu hình MySQL cho website: {domain}")
        return

    os.makedirs(target_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    filename = f"db_{domain}_{timestamp}.sql"
    filepath = os.path.join(target_folder, filename)

    
    run_mysql_dump(site_config.mysql.db_name, "/tmp/export.sql")
    mysql_container.copy_from("/tmp/export.sql", filepath)
    info(f"✅ Đã xuất database cho {domain} đến: {filepath}")


@log_call
def import_database(domain: str, db_file: str, reset: bool = True):
    site_config = get_site_config(domain)
    if not site_config or not site_config.mysql:
        error(f"❌ Không tìm thấy cấu hình MySQL cho website: {domain}")
        return

    db_name = site_config.mysql.db_name


    if reset:
        run_mysql_command(f"DROP DATABASE IF EXISTS {db_name}; CREATE DATABASE {db_name};")
        info(f"🗑️ Đã reset database {db_name} trước khi import.")

    mysql_container.copy_to(db_file, "/tmp/import.sql")
    run_mysql_import("/tmp/import.sql", db_name)
    info(f"✅ Đã import dữ liệu từ {db_file} vào database {db_name} cho website {domain}.")

# File: core/backend/modules/mysql/mysql_exec.py

from core.backend.modules.mysql.utils import detect_mysql_client
from core.backend.modules.mysql.utils import get_mysql_root_password
from core.backend.objects.container import Container
from core.backend.utils.env_utils import env_required, env

env_required(["MYSQL_CONTAINER_NAME"])
mysql_container = Container(env["MYSQL_CONTAINER_NAME"])



def run_mysql_command(query: str, db: str = None):
    """Thực thi lệnh mysql trong container"""
    container = mysql_container
    client = detect_mysql_client(container)
    pwd = get_mysql_root_password()
    db_part = db or ""
    cmd = f"{client} -u root {db_part} -e \"{query}\""
    return container.exec(["sh", "-c", cmd], user="root", envs={"MYSQL_PWD": pwd})


def run_mysql_import(sql_path: str, db: str):
    """Import file SQL vào DB trong container"""
    container = mysql_container
    client = detect_mysql_client(container)
    pwd = get_mysql_root_password()
    cmd = f"{client} -u root {db} < {sql_path}"
    return container.exec(["sh", "-c", cmd], user="root", envs={"MYSQL_PWD": pwd})


def run_mysql_dump(db: str, output_path_in_container: str):
    """Dump file SQL từ DB trong container"""
    container = mysql_container
    client = detect_mysql_client(container)
    pwd = get_mysql_root_password()
    dump_cmd = "mariadb-dump" if client == "mariadb" else "mysqldump"
    cmd = f"{dump_cmd} -u root {db} > {output_path_in_container}"
    return container.exec(["sh", "-c", cmd], user="root", envs={"MYSQL_PWD": pwd})

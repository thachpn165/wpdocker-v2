from core.backend.utils.system_info import get_total_ram_mb, get_total_cpu_cores
from core.backend.objects.container import Container
from core.backend.utils.env_utils import env, env_required
from core.backend.utils.crypto import encrypt, decrypt
from core.backend.objects.config import Config
from core.backend.utils.password import strong_password
from core.backend.utils.debug import debug, info, warn, error, log_call, success
import questionary

@log_call
def run_mysql_bootstrap():
    config = Config()

    env_required([
        "PROJECT_NAME",
        "MYSQL_CONTAINER_NAME",
        "MYSQL_VOLUME_NAME",
        "DOCKER_NETWORK",
        "INSTALL_DIR",
        "CONFIG_DIR",
    ])

    mysql_container = env["MYSQL_CONTAINER_NAME"]
    volume_name = env["MYSQL_VOLUME_NAME"]
    docker_network = env["DOCKER_NETWORK"]
    project_name = env["PROJECT_NAME"]

    # Hỏi chọn phiên bản nếu chưa có
    if not config.get("mysql.version"):
        version_choices = [
            {"name": "MariaDB Latest", "value": "mariadb:latest"},
            {"name": "MariaDB 10.5", "value": "mariadb:10.5"},
            {"name": "MariaDB 10.6", "value": "mariadb:10.6"},
            {"name": "MariaDB 10.11", "value": "mariadb:10.11"},
        ]
        selected = questionary.select(
            "📦 Chọn phiên bản MariaDB muốn sử dụng:",
            choices=version_choices
        ).ask()
        config.set("mysql.version", selected)
        config.save()
        success(f"✅ Đã lưu phiên bản MariaDB: {selected}")

    mysql_image = config.get("mysql.version") or "mariadb:10.11"

    if config.get("mysql.root_passwd"):
        passwd = decrypt(config.get("mysql.root_passwd"))
    else:
        passwd = strong_password()
        config.set("mysql.root_passwd", encrypt(passwd))
        config.save()
        debug("Đã lưu mật khẩu MySQL vào config.")
        debug("Plain password:", passwd)
        debug("Encrypted password (in config):", config.get("mysql.root_passwd")) 
    import os
    config_dir = env["CONFIG_DIR"]
    os.makedirs(config_dir, exist_ok=True)

    config_path = os.path.join(config_dir, "mysql.conf")
    if not os.path.exists(config_path):
        info(f"Đang tạo cấu hình MySQL tại: {config_path}")

        total_ram = get_total_ram_mb()
        total_cpu = get_total_cpu_cores()

        max_connections = max(total_ram // 4, 100)
        query_cache_size = 32
        innodb_buffer_pool_size = max(total_ram // 2, 256)
        innodb_log_file_size = max(innodb_buffer_pool_size // 6, 64)
        table_open_cache = max(total_ram * 8, 400)
        thread_cache_size = max(total_cpu * 8, 16)

        with open(config_path, "w") as f:
            f.write(f"""[mysqld]
max_connections = {max_connections}
query_cache_size = {query_cache_size}M
innodb_buffer_pool_size = {innodb_buffer_pool_size}M
innodb_log_file_size = {innodb_log_file_size}M
table_open_cache = {table_open_cache}
thread_cache_size = {thread_cache_size}
""")
        success("Đã tạo file cấu hình MySQL thành công.")
    else:
        debug(f"File cấu hình MySQL đã tồn tại: {config_path}")

    container = Container(
        name=mysql_container,
        template_path=env["INSTALL_DIR"] + "/core/templates/docker-compose.mysql.yml.template",
        output_path=env["INSTALL_DIR"] + "/docker-compose/docker-compose.mysql.yml",
        env_map={
            "PROJECT_NAME": project_name,
            "MYSQL_CONTAINER_NAME": mysql_container,
            "MYSQL_IMAGE": mysql_image,
            "MYSQL_VOLUME_NAME": volume_name,
            "DOCKER_NETWORK": docker_network,
        },
        sensitive_env={"mysql_root_passwd": passwd}
    )

    container.ensure_ready()
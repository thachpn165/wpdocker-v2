from core.backend.objects.container import Container
from core.backend.utils.env_utils import env_required
from core.backend.utils.crypto import encrypt, decrypt
from core.backend.objects.config import Config
from core.backend.utils.password import strong_password

def run_mysql_bootstrap():
    config = Config()

    env = env_required([
        "PROJECT_NAME",
        "MYSQL_CONTAINER_NAME",
        "MYSQL_IMAGE",
        "MYSQL_VOLUME_NAME",
        "DOCKER_NETWORK",
        "INSTALL_DIR",
    ])

    mysql_container = env["MYSQL_CONTAINER_NAME"]
    mysql_image = env["MYSQL_IMAGE"]
    volume_name = env["MYSQL_VOLUME_NAME"]
    docker_network = env["DOCKER_NETWORK"]
    project_name = env["PROJECT_NAME"]

    if config.get("mysql.root_passwd"):
        passwd = decrypt(config.get("mysql.root_passwd"))
    else:
        passwd = strong_password()
        config.set("mysql.root_passwd", encrypt(passwd))
        config.save()
        print("🔑 Đã lưu mật khẩu MySQL vào config.")
        
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

    if not container.exists():
        print("📦 MySQL chưa tồn tại. Đang triển khai...")
        container.generate_compose_file()
        container.up()
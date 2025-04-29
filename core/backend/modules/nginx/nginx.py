# File: core/backend/modules/nginx/nginx.py

from core.backend.utils.debug import info, debug, warn, error, log_call
from core.backend.utils.env_utils import env
from core.backend.objects.compose import Compose
from core.backend.objects.container import Container
import os

# 🐳 Khởi tạo compose NGINX một lần duy nhất
container_name = env.get("NGINX_CONTAINER_NAME")
install_dir = env.get("INSTALL_DIR")

if container_name and install_dir:
    docker_compose_file = os.path.join(install_dir, "docker-compose", "docker-compose.nginx.yml")
    compose_nginx = Compose(name=container_name, output_path=docker_compose_file)
else:
    compose_nginx = None

@log_call
def test_config():
    if not compose_nginx:
        error("❌ Không tìm thấy thông tin container NGINX.")
        return False
    try:
        container = Container(name=container_name)
        container.exec(["openresty", "-t"])
        info("✅ Cấu hình NGINX hợp lệ.")
        return True
    except Exception as e:
        error(f"❌ Lỗi kiểm tra cấu hình NGINX: {e}")
        return False

@log_call 
def reload():
    if not compose_nginx:
        error("❌ Không tìm thấy thông tin container NGINX.")
        return
    if not test_config():
        warn("⚠️ Bỏ qua reload do lỗi cấu hình.")
        return
    try:
        container = Container(name=container_name)
        container.exec(["openresty", "-s", "reload"])
        info("🔄 Reload NGINX thành công.")
    except Exception as e:
        error(f"❌ Lỗi khi reload NGINX: {e}")

@log_call
def restart():
    if not compose_nginx:
        error("❌ Không tìm thấy thông tin container NGINX.")
        return
    if not os.path.isfile(compose_nginx.output_path):
        error(f"❌ Không tìm thấy file docker-compose: {compose_nginx.output_path}")
        return
    try:
        compose_nginx.down()
        compose_nginx.up(force_recreate=True)
        info("🔁 Restart NGINX thành công.")
    except Exception as e:
        error(f"❌ Lỗi khi restart NGINX: {e}")
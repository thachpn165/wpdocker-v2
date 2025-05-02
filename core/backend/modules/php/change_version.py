import os
import requests
from core.backend.objects.config import Config
from core.backend.objects.compose import Compose
from core.backend.modules.php.utils import get_php_container_name
from core.backend.utils.env_utils import env
from core.backend.utils.debug import debug, error, info
from core.backend.modules.website.website_utils import get_site_config, set_site_config
from core.backend.modules.php.init_client import init_php_client
from rich.progress import Progress, SpinnerColumn, TextColumn

BITNAMI_IMAGE_PREFIX = "bitnami/php-fpm"
DOCKER_HUB_URL = "https://hub.docker.com/v2/repositories/{image}/tags/{version}"

def php_change_version(domain: str, php_version: str):
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task(f"Kiểm tra phiên bản PHP {php_version} trên Docker Hub...", total=None)

            image_url = DOCKER_HUB_URL.format(
                image=BITNAMI_IMAGE_PREFIX.replace('/', '%2F'),
                version=php_version
            )
            response = requests.get(image_url)

            if response.status_code != 200:
                progress.stop()
                error(f"❌ Phiên bản PHP {php_version} không tồn tại trên Docker Hub!")
                return

            progress.update(task, description=f"Đang cập nhật config của {domain}...")
            site_config = get_site_config(domain)
            if not site_config:
                progress.stop()
                error(f"❌ Không tìm thấy config cho domain: {domain}")
                return

            site_config.php_version = php_version
            set_site_config(domain, site_config)
            info(f"📦 Đã cập nhật config: PHP version → {php_version}")

            compose_file_path = os.path.join(env["SITES_DIR"], domain, "docker-compose.php.yml")
            if not os.path.isfile(compose_file_path):
                progress.stop()
                error(f"❌ Không tìm thấy file: {compose_file_path}")
                return

            progress.update(task, description="Cập nhật docker-compose.php.yml...")
            with open(compose_file_path, "r") as f:
                lines = f.readlines()

            with open(compose_file_path, "w") as f:
                for line in lines:
                    if "bitnami/php-fpm:" in line:
                        indent = line[:len(line) - len(line.lstrip())]
                        f.write(f"{indent}image: bitnami/php-fpm:{php_version}\n")
                    else:
                        f.write(line)

            progress.update(task, description="Rebuild container PHP...")
            container_name = get_php_container_name(domain)
            compose = Compose(name=f"{container_name}", output_path=compose_file_path)
            compose.down()
            compose.up(force_recreate=True)
            compose.ensure_ready()

        # ✅ Sử dụng init_php_client để khởi tạo container chuẩn
        try:
            container = init_php_client(domain)
            output = container.exec(["php", "-v"])
            if output:
                print("\n📋 Thông tin phiên bản PHP:")
                print(output)
        except Exception as e:
            error(f"❌ Không thể kiểm tra phiên bản PHP từ container: {e}")

        info(f"✅ Đã thay đổi và rebuild PHP {php_version} cho {domain} thành công.")

    except Exception as e:
        error(f"❌ Lỗi khi thay đổi phiên bản PHP: {str(e)}")

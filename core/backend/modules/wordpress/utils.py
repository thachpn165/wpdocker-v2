# File: core/backend/modules/wordpress/wordpress_utils.py

from core.backend.modules.php.utils import get_php_container_name
from core.backend.objects.container import Container
from core.backend.utils.debug import log_call, debug, info, error

@log_call
def run_wp_cli(domain: str, args: list[str]) -> str:
    """
    Thực thi lệnh WP CLI bên trong container PHP tương ứng với domain.

    Args:
        domain (str): Tên domain website.
        args (list[str]): Danh sách tham số lệnh WP CLI cần chạy, ví dụ ['core', 'install', '--url=...', '--title=...']

    Returns:
        str: Output của lệnh WP CLI nếu thành công, hoặc None nếu lỗi.
    """
    container_name = get_php_container_name(domain)
    container = Container(name=container_name)

    if not container.running():
        error(f"❌ Container PHP {container_name} không chạy.")
        return None

    try:
        cmd = ["wp"] + args
        result = container.exec(cmd, workdir="/var/www/html")
        debug(f"WP CLI Output: {result}")
        return result
    except Exception as e:
        error(f"❌ Lỗi khi thực thi WP CLI: {e}")
        return None
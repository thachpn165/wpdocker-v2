from core.backend.utils.system_info import get_total_cpu_cores, get_total_ram_mb
import os
from core.backend.utils.env_utils import env, env_required
from core.backend.objects.config import Config
from core.backend.utils.debug import log_call, debug, error, info, warn
from core.backend.objects.container import Container
import jsons
from typing import Optional
from core.backend.models.config import SiteConfig
from questionary import select
# Kiểm tra website có tồn tại hay không
@log_call
def _is_website_exists(domain: str) -> bool:
    config = Config()
    sites_dir = env["SITES_DIR"]
    site_dir = os.path.join(sites_dir, domain)
    site_dir_exists = os.path.isdir(site_dir)

    site_data = config.get().get("site", {})
    config_exists = domain in site_data  # check domain có nằm trong site_data không

    debug(
        f"site_dir_exists: {site_dir_exists}, config_exists: {config_exists}")
    return site_dir_exists and config_exists

# Kiểm tra website có đang chạy hay không
# Trả về lý do cụ thể cho từng trường hợp
@log_call
def _is_website_running(domain: str) -> str:
    if not _is_website_exists(domain):
        return "❌ Không hợp lệ (thiếu thư mục hoặc config)"

    php_container = Container(f"{domain}-php")
    if not php_container.running():
        return "❌ Container PHP không hoạt động"

    nginx_conf = os.path.join(env["CONFIG_DIR"], "nginx", "conf.d", f"{domain}.conf")
    if not os.path.isfile(nginx_conf):
        return "❌ Thiếu cấu hình NGINX"

    return "✅ Đang chạy"

# Tính toán các thông số PHP-FPM dựa trên tài nguyên server
# và nhóm tài nguyên (thấp, trung bình, cao)

def website_calculate_php_fpm_values():
    total_ram = get_total_ram_mb()  # MB
    total_cpu = get_total_cpu_cores()  # Số core

    # Xác định nhóm tài nguyên server
    is_low = total_cpu < 2 or total_ram < 2048
    is_high = total_cpu >= 8 and total_ram >= 8192
    is_medium = not is_low and not is_high

    # Thiết lập tham số theo nhóm
    if is_low:
        reserved_ram = 384
        avg_process_size = 40
        pm_mode = "ondemand"
        cpu_multiplier = 3
    elif is_medium:
        reserved_ram = 512
        avg_process_size = 50
        pm_mode = "ondemand"
        cpu_multiplier = 5
    else:  # is_high
        reserved_ram = 1024
        avg_process_size = 60
        pm_mode = "dynamic"
        cpu_multiplier = 8

    available_ram = total_ram - reserved_ram
    ram_based_max = available_ram // avg_process_size
    cpu_based_max = total_cpu * cpu_multiplier
    max_children = min(ram_based_max, cpu_based_max)
    max_children = max(max_children, 4)

    if pm_mode == "dynamic":
        start_servers = min(total_cpu + 2, max_children)
        min_spare_servers = min(total_cpu, start_servers)
        max_spare_servers = min(total_cpu * 3, max_children)
    else:
        start_servers = 0
        min_spare_servers = 0
        max_spare_servers = min(total_cpu * 2, max_children)

    min_spare_servers = max(min_spare_servers, 1)
    max_spare_servers = max(max_spare_servers, 2)

    return {
        "pm_mode": pm_mode,
        "max_children": max_children,
        "start_servers": start_servers,
        "min_spare_servers": min_spare_servers,
        "max_spare_servers": max_spare_servers,
        "total_cpu": total_cpu,
        "total_ram": total_ram,
    }

# Lấy danh sách các website đã được tạo


def website_list():
    config = Config()
    raw_sites = config.get().get("site", {})
    debug(f"Website raw config: {raw_sites}")

    valid_domains = []
    for domain in raw_sites.keys():
        if _is_website_exists(domain):
            valid_domains.append(domain)

    debug(f"Website valid domains: {valid_domains}")
    return valid_domains

# Kiểm tra phân quyền www-data cho thư mục trong container


def ensure_www_data_ownership(container_name, path_in_container):
    container = Container(name=container_name)
    debug(
        f"🔍 Kiểm tra quyền sở hữu tại {path_in_container} trong container {container_name}")
    container.exec(["chown", "-R", "www-data:www-data",
                   path_in_container], user="root")
    info(
        f"✅ Đã đảm bảo phân quyền www-data cho {path_in_container} trong container {container_name}")


def get_site_config(domain: str) -> Optional[SiteConfig]:
    config = Config()
    raw_sites = config.get().get("site", {})
    site_raw = raw_sites.get(domain)
    if not site_raw:
        return None
    try:
        return jsons.load(site_raw, SiteConfig)
    except Exception as e:
        debug(f"❌ Lỗi khi load SiteConfig cho {domain}: {e}")
        return None


def set_site_config(domain: str, site_config: SiteConfig) -> None:
    config = Config()
    site_data = config.get().get("site", {})
    site_data[domain] = jsons.dump(site_config, strict=True) 
    config.update_key("site", site_data)
    config.save()


def delete_site_config(domain: str, subkey: Optional[str] = None) -> bool:
    config = Config()
    site_data = config.get().get("site", {})
    if domain not in site_data:
        return False

    if subkey:
        if subkey in site_data[domain]:
            del site_data[domain][subkey]
            config.update_key("site", site_data)
            config.save()
            return True
        return False
    else:
        # Xóa toàn bộ domain
        del site_data[domain]
        config.update_key("site", site_data)
        config.save()
        return True

# Chọn website từ danh sách
def select_website(message: str = "Chọn website:", default: Optional[str] = None) -> Optional[str]:
    """Hiển thị danh sách website và cho phép chọn. Trả về None nếu người dùng huỷ thao tác."""
    websites = website_list()
    if not websites:
        warn("Không tìm thấy website nào.")
        return None

    try:
        return select(
            message,
            choices=websites,
            default=default if default in websites else None
        ).ask()
    except (KeyboardInterrupt, EOFError):
        info("Đã huỷ thao tác.")
        return None

# Lấy đường dẫn thư mục chứa các website
def get_sites_dir():
    #env_required("SITES_DIR")
    """Helper function to handle sites_dir correctly whether it's a string or dictionary."""
    sites_dir = env["SITES_DIR"]
    if isinstance(sites_dir, dict):
        debug(f"Sites dir is a dictionary: {sites_dir}")
        sites_dir = sites_dir.get("path", "/opt/wp-docker/data/sites")
    return sites_dir
import os
from core.backend.utils.env_utils import env
from core.backend.objects.config import Config
from core.backend.utils.debug import log_call, debug, error

@log_call
def _is_website_exists(domain: str) -> bool:
    config = Config()
    sites_dir = env["SITES_DIR"]
    site_dir = os.path.join(sites_dir, domain)

    # Kiểm tra thư mục site và config trong .config.json
    site_dir_exists = os.path.isdir(site_dir)
    config_exists = config.get(f"site.{domain}") is not None
    debug(f"site_dir_exists: {site_dir_exists}, config_exists: {config_exists}")
    return site_dir_exists and config_exists

    
from core.backend.utils.system_info import get_total_cpu_cores, get_total_ram_mb

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
# Return: array danh sách tên miền
def website_list():
    config = Config()
    sites = config.get("site", {})
    return [domain for domain in sites if _is_website_exists(domain)]
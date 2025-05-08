"""
Entrypoint for setting up cache for WordPress and configuring NGINX.
This module is designed for extensibility and separation of concerns.
"""

from src.common.logging import error
from src.common.utils.validation import is_valid_domain
from src.features.cache.core.fastcgi import setup_fastcgi_cache
from src.features.cache.constants import CACHE_TYPES
# Có thể import thêm các loại cache khác trong tương lai, ví dụ:
# from src.features.cache.core.w3total import setup_w3total_cache
# from src.features.cache.core.supercache import setup_super_cache


def setup_cache(domain: str, cache_type: str) -> bool:
    """
    Entrypoint tổng cho cài đặt cache. Ghi nhận lựa chọn cache_type và gọi submodule phù hợp.
    """
    if not is_valid_domain(domain):
        error(f"Invalid domain: {domain}")
        return False
    if cache_type == "fastcgi-cache":
        return setup_fastcgi_cache(domain)
    # Có thể mở rộng cho các loại cache khác:
    # elif cache_type == "w3-total-cache":
    #     return setup_w3total_cache(domain)
    # elif cache_type == "wp-super-cache":
    #     return setup_super_cache(domain)
    else:
        error(f"Cache type '{cache_type}' is not supported yet.")
        return False 
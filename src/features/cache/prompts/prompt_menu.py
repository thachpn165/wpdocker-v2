"""
WP Cache setup menu prompt module.

This module provides the user interface for WordPress cache setup functions
like installing and configuring different caching plugins and systems.
"""

import questionary
from questionary import Style
from typing import Optional
from src.features.cache.core.setup import setup_fastcgi_cache, setup_cache
from src.common.logging import info, error, debug, success
from src.features.website.utils import select_website
from src.features.cache.constants import CACHE_TYPES

def not_implemented() -> None:
    """Handle not implemented features."""
    error("🚧 Feature not implemented yet")
    input("Press Enter to continue...")

# Custom style for the menu
custom_style = Style([
    ('qmark', 'fg:cyan bold'),
    ('question', 'fg:cyan bold'),
    ('answer', 'fg:green bold'),
    ('pointer', 'fg:cyan bold'),
    ('highlighted', 'fg:green bold'),
    ('selected', 'fg:green bold'),
    ('separator', 'fg:cyan'),
    ('instruction', 'fg:gray'),
    ('text', ''),
    ('disabled', 'fg:gray italic'),
])

def prompt_cache_menu() -> None:
    """Hiển thị menu quản lý cache cho website WordPress."""
    while True:
        answer = questionary.select(
            "\n🗄️ Cache Management Menu:",
            choices=[
                {"name": f"1. Cài đặt {CACHE_TYPES[0].replace('-', ' ').title()} cho WordPress", "value": CACHE_TYPES[0]},
                {"name": f"2. Cài đặt {CACHE_TYPES[1].replace('-', ' ').title()} cho WordPress", "value": CACHE_TYPES[1]},
                {"name": f"3. Cài đặt {CACHE_TYPES[2].replace('-', ' ').title()} cho WordPress", "value": CACHE_TYPES[2]},
                {"name": f"4. Cài đặt {CACHE_TYPES[3].replace('-', ' ').title()} cho WordPress", "value": CACHE_TYPES[3]},
                {"name": f"5. Tắt toàn bộ cache (No Cache)", "value": CACHE_TYPES[4]},
                {"name": "0. Quay lại menu chính", "value": "exit"},
            ]
        ).ask()
        if answer in (CACHE_TYPES[0], CACHE_TYPES[1], CACHE_TYPES[2], CACHE_TYPES[3], CACHE_TYPES[4]):
            domain = select_website("Chọn website cần cài cache hoặc tắt cache:")
            if not domain:
                info("Không có website nào hoặc thao tác bị hủy. Quay lại menu.")
                continue
            if setup_cache(domain, answer):
                info(f"Đã cài đặt {answer} thành công cho {domain}")
            else:
                error(f"Cài đặt {answer} thất bại cho {domain}")
        elif answer == "exit":
            break
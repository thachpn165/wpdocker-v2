"""
WP Cache setup menu prompt module.

This module provides the user interface for WordPress cache setup functions
like installing and configuring different caching plugins and systems.
"""

import questionary
from questionary import Style
from typing import Optional
from src.features.cache.core.setup import setup_fastcgi_cache
from src.common.logging import info, error, debug, success
from src.features.website.utils import select_website

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
                {"name": "1. Cài đặt FastCGI Cache cho WordPress", "value": "fastcgi"},
                {"name": "0. Quay lại menu chính", "value": "exit"},
            ]
        ).ask()
        if answer == "fastcgi":
            domain = select_website("Chọn website cần cài cache:")
            if not domain:
                info("Không có website nào hoặc thao tác bị hủy. Quay lại menu.")
                continue
            if setup_fastcgi_cache(domain):
                info(f"Đã cài đặt FastCGI cache thành công cho {domain}")
            else:
                error(f"Cài đặt FastCGI cache thất bại cho {domain}")
        elif answer == "exit":
            break
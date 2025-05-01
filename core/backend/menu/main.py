# File: core/menu/main.py
import sys
from rich.console import Console
from rich.text import Text
from core.backend.objects.menu import Menu, MenuItem
from core.backend.modules.website.prompts.create_prompt import prompt_create_website
from core.backend.modules.website.prompts.delete_prompt import prompt_delete_website
from core.backend.modules.website.prompts.list_prompt import prompt_list_website
from core.backend.modules.website.prompts.restart_prompt import prompt_restart_website
from core.backend.modules.website.prompts.logs_prompt import prompt_watch_logs
from core.backend.modules.website.prompts.info_prompt import prompt_info_website
from core.backend.modules.ssl.prompts.install_prompt import prompt_install_ssl
from core.backend.modules.ssl.prompts.check_prompt import prompt_check_ssl

console = Console()

def display_header():
    header = Text("""

    ██╗    ██╗██████╗     ██████╗  ██████╗  ██████╗██╗  ██╗███████╗██████╗ 
    ██║    ██║██╔══██╗    ██╔══██╗██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
    ██║ █╗ ██║██████╔╝    ██████╔╝██║   ██║██║     █████╔╝ █████╗  ██████╔╝
    ██║███╗██║██╔═══╝     ██╔═══╝ ██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
    ╚███╔███╔╝██║         ██║     ╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║
     ╚══╝╚══╝ ╚═╝         ╚═╝      ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    ═══════════════════════════════════════════════════════════════════════════════
    """, style="cyan")
    console.print(header)

def show_main_menu():
    display_header()
    menu = Menu(
        title="\n📋 Chọn chức năng cần sử dụng:",
        items=[
            MenuItem("1", "Quản lý Website", website_menu),
            MenuItem("2", "Quản lý Chứng chỉ SSL", ssl_menu),
            MenuItem("3", "Công cụ hệ thống", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("4", "Quản lý RClone", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("5", "Công cụ WordPress", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("6", "Quản lý Backup", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("7", "Cài đặt Cache WP", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("8", "Quản lý PHP", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("9", "Quản lý Database", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("10", "Kiểm tra & cập nhật WP Docker", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("0", "Thoát", lambda: sys.exit(console.print("👋 Tạm biệt!", style="bold green")))
        ],
        back_id="0"
    )
    menu.display()

def website_menu():
    menu = Menu(
        title="\n🌐 Quản lý Website:",
        items=[
            MenuItem("1", "Tạo website", prompt_create_website),
            MenuItem("2", "Xóa website", prompt_delete_website),
            MenuItem("3", "Xem danh sách website", prompt_list_website),
            MenuItem("4", "Restart lại website", prompt_restart_website),
            MenuItem("5", "Xem logs website", prompt_watch_logs),
            MenuItem("6", "Xem thông tin website", prompt_info_website),
            MenuItem("7", "Migrate dữ liệu về WP Docker", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("0", "Quay lại menu chính", None)
        ],
        back_id="0"
    )
    menu.display()

def ssl_menu():
    menu = Menu(
        title="\n🔒 Quản lý Chứng chỉ SSL:",
        items=[
            MenuItem("1", "Tạo chứng chỉ tự ký", lambda: prompt_install_ssl("selfsigned")),
            MenuItem("2", "Tạo chứng chỉ Lets Encrypt (Miễn phí)", lambda: prompt_install_ssl("letsencrypt")),
            MenuItem("3", "Cài chứng chỉ thủ công (trả phí)", lambda: prompt_install_ssl("manual")),
            MenuItem("4", "Kiểm tra thông tin chứng chỉ", prompt_check_ssl),
            MenuItem("5", "Sửa chứng chỉ hiện tại", lambda: console.print("🚧 Chức năng đang được phát triển...")),
            MenuItem("0", "Quay lại menu chính", None)
        ],
        back_id="0"
    )
    menu.display()

# File: core/menu/main.py
import questionary
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
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

    main_options = {
        "[1] Quản lý Website": website_menu,
        "[2] Quản lý Chứng chỉ SSL": ssl_menu,
        "[3] Công cụ hệ thống": lambda: console.print("🚧 Chức năng đang được phát triển..."),
        "[4] Quản lý RClone": lambda: console.print("🚧 Chức năng đang được phát triển..."),
        "[5] Công cụ WordPress": lambda: console.print("🚧 Chức năng đang được phát triển..."),
        "[6] Quản lý Backup": lambda: console.print("🚧 Chức năng đang được phát triển..."),
        "[7] Cài đặt Cache WP": lambda: console.print("🚧 Chức năng đang được phát triển..."),
        "[8] Quản lý PHP": lambda: console.print("🚧 Chức năng đang được phát triển..."),
        "[9] Quản lý Database": lambda: console.print("🚧 Chức năng đang được phát triển..."),
        "[10] Kiểm tra & cập nhật WP Docker": lambda: console.print("🚧 Chức năng đang được phát triển..."),
        "[11] Thoát": lambda: sys.exit(console.print("👋 Tạm biệt!", style="bold green"))
    }

    while True:
        answer = questionary.select(
            "\n Chọn chức năng cần sử dụng:",
            choices=list(main_options.keys())
        ).ask()

        console.print(f"👉 [yellow]Bạn chọn:[/] {answer[4:]}")
        action = main_options.get(answer)
        if action:
            action()
            input("\n⏎ Nhấn Enter để quay lại menu...")

def website_menu():
    website_options = {
        "[1] Tạo website": prompt_create_website,
        "[2] Xóa website": prompt_delete_website,
        "[3] Xem danh sách website": prompt_list_website,
        "[4] Restart lại website": prompt_restart_website,
        "[5] Xem logs website": prompt_watch_logs,
        "[6] Xem thông tin website": prompt_info_website,
        "[7] Migrate dữ liệu về WP Docker": lambda: console.print("🚧 Chức năng đang được phát triển..."),
        "[8] Quay lại menu chính": None
    }

    while True:
        answer = questionary.select(
            "\n🌐 Quản lý Website:",
            choices=list(website_options.keys())
        ).ask()

        if answer == "[8] Quay lại menu chính":
            return

        console.print(f"👉 [yellow]Bạn chọn:[/] {answer[4:]}")
        action = website_options.get(answer)
        if action:
            action()
            input("\n⏎ Nhấn Enter để quay lại menu...")

def ssl_menu():
    ssl_options = {
        "[1] Tạo chứng chỉ tự ký": lambda: prompt_install_ssl("selfsigned"),
        "[2] Tạo chứng chỉ Lets Encrypt (Miễn phí)": lambda: prompt_install_ssl("letsencrypt"),
        "[3] Cài chứng chỉ thủ công (trả phí)": lambda: prompt_install_ssl("manual"),
        "[4] Kiểm tra thông tin chứng chỉ": prompt_check_ssl,
        "[5] Sửa chứng chỉ hiện tại": lambda: console.print("🚧 Chức năng đang được phát triển..."),
        "[6] Quay lại menu chính": None
    }

    while True:
        answer = questionary.select(
            "\n🔒 Quản lý Chứng chỉ SSL:",
            choices=list(ssl_options.keys())
        ).ask()

        if answer == "[6] Quay lại menu chính":
            return

        console.print(f"👉 [yellow]Bạn chọn:[/] {answer[4:]}")
        action = ssl_options.get(answer)
        if action:
            action()
            input("\n⏎ Nhấn Enter để quay lại menu...")

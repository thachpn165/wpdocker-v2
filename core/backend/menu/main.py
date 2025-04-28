# File: core/menu/main.py
import questionary
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from core.backend.modules.website.prompts.create_prompt import prompt_create_website

console = Console()

menu_items = [
    ("Website Management", "website_menu"),
    ("SSL Certificate Management", "ssl_menu"),
    ("System Tools", "system_tools_menu"),
    ("RClone Management", "rclone_menu"),
    ("WordPress Tools", "wordpress_tools_menu"),
    ("Backup Management", "backup_menu"),
    ("WordPress Cache Setup", "wp_cache_menu"),
    ("PHP Management", "php_menu"),
    ("Database Management", "db_menu"),
    ("Check & Update WP Docker", "update_menu"),
    ("Exit", "exit")
]

def display_header():
    header = Text("""
    ============================================
    ██╗    ██╗██████╗     ██████╗  ██████╗  ██████╗██╗  ██╗███████╗██████╗ 
    ██║    ██║██╔══██╗    ██╔══██╗██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
    ██║ █╗ ██║██████╔╝    ██████╔╝██║   ██║██║     █████╔╝ █████╗  ██████╔╝
    ██║███╗██║██╔═══╝     ██╔═══╝ ██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
    ╚███╔███╔╝██║         ██║     ╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║
     ╚══╝╚══╝ ╚═╝         ╚═╝      ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    ============================================
    """, style="bold cyan")
    console.print(header)

def show_main_menu():
    display_header()

    choices = [f"[{i+1}] {item[0]}" for i, item in enumerate(menu_items)]
    answer = questionary.select(
        "\n🔧 Enter the corresponding menu option number:",
        choices=choices
    ).ask()

    selected_index = choices.index(answer)
    selected_key = menu_items[selected_index][1]

    if selected_key == "exit":
        console.print("👋 Tạm biệt!", style="bold green")
        sys.exit(0)

    if selected_key == "website_menu":
        website_menu()
        show_main_menu()
    else:
        console.print(f"👉 [yellow]Bạn chọn:[/] {menu_items[selected_index][0]}")
        console.print("🚧 Chức năng đang được phát triển...")

        input("\n⏎ Nhấn Enter để quay lại menu...")
        show_main_menu()

def website_menu():
    while True:
        choices = [
            "[1] Tạo website",
            "[2] Xóa website",
            "[3] Xem danh sách website",
            "[4] Restart lại website",
            "[5] Xem logs website",
            "[6] Xem thông tin website",
            "[7] Migrate dữ liệu về WP Docker",
            "[8] Quay lại menu chính"
        ]
        answer = questionary.select(
            "\n🌐 Quản lý Website:",
            choices=choices
        ).ask()

        selected_index = choices.index(answer)
        console.print(f"👉 [yellow]Bạn chọn:[/] {choices[selected_index][4:]}")

        if answer == choices[-1]:
            return  # Quay lại menu chính
        elif answer == choices[0]:  # Tạo website
            prompt_create_website()
        else:
            console.print("🚧 Chức năng đang được phát triển...")

        input("\n⏎ Nhấn Enter để quay lại menu...")
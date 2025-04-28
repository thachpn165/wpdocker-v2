# File: core/menu/main.py
import questionary
import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

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

    console.print(f"👉 [yellow]Bạn chọn:[/] {menu_items[selected_index][0]}")
    console.print("🚧 Chức năng đang được phát triển...")

    input("\n⏎ Nhấn Enter để quay lại menu...")
    show_main_menu()
# File: core/backend/menu_main.py

from core_loader import init
env = init()
import sys
import questionary

# Load bootstrap modules
from bootstraps.config_bootstrap import run_config_bootstrap
from bootstraps.system_bootstrap import run_system_bootstrap
install_dir = env["INSTALL_DIR"]

# ==============================
# 📋 Menu chính
# ==============================
def main_menu():
    while True:
        choice = questionary.select(
            "🔧 Chọn tính năng:",
            choices=[
                "🌐 Quản lý Website",
                "📦 Quản lý Backup",
                "🔐 Quản lý SSL",
                "⚙️ Hệ thống",
                "❌ Thoát"
            ]
        ).ask()

        if choice == "🌐 Quản lý Website":
            website_menu()
        elif choice == "📦 Quản lý Backup":
            backup_menu()
        elif choice == "🔐 Quản lý SSL":
            ssl_menu()
        elif choice == "⚙️ Hệ thống":
            system_menu()
        elif choice == "❌ Thoát":
            print("👋 Tạm biệt!")
            sys.exit(0)

# ==============================
# 🌐 Menu Website
# ==============================
def website_menu():
    ...

# ==============================
# 📦 Menu Backup
# ==============================
def backup_menu():
    ...

# ==============================
# 🔐 Menu SSL
# ==============================
def ssl_menu():
    ...

# ==============================
# ⚙️ Menu Hệ thống
# ==============================
def system_menu():
    ...

# ==============================
# 🚀 Chạy chương trình
# ==============================

if __name__ == "__main__":
    run_config_bootstrap()
    run_system_bootstrap()
    main_menu()
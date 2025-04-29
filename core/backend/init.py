# File: core/backend/menu_main.py

from core_loader import init
env = init()

import sys
import questionary

# Load bootstrap modules
from bootstraps.config_bootstrap import run_config_bootstrap
from bootstraps.system_bootstrap import run_system_bootstrap
from bootstraps.docker_bootstrap import run_docker_bootstrap
from bootstraps.mysql_bootstrap import run_mysql_bootstrap
from bootstraps.webserver_bootstrap import run_webserver_bootstrap
from bootstraps.wpcli_bootstrap import run_wpcli_bootstrap
from bootstraps.redis_bootstrap import run_redis_bootstrap
from bootstraps.misc_bootstrap import run_misc_bootstrap
from menu.main import show_main_menu

install_dir = env["INSTALL_DIR"]


# ==============================
# 🚀 Chạy chương trình
# ==============================

if __name__ == "__main__":
    run_config_bootstrap()
    run_system_bootstrap()
    run_docker_bootstrap()
    run_mysql_bootstrap()
    run_webserver_bootstrap()
    run_wpcli_bootstrap()
    run_redis_bootstrap()
    run_misc_bootstrap()
    # Chạy menu chính 
    show_main_menu()
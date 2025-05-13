#!/usr/bin/env python3
"""
Main entry point for the WP Docker application.

This module provides the main entry point for the application,
initializing the environment and starting the menu system.
"""

import sys

from src.common.logging import info, error, debug, enable_exception_hook, success
from src.common.utils.environment import env, env_required
from src.core.init import initialize_system
from src.core.loader import load_core

# For terminal menu
import questionary
from questionary import Style
from rich.console import Console
from rich.text import Text

# Console for rich output
console = Console()

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


def display_banner() -> None:
    """Display application banner."""
    # Clear screen
    # os.system('clear' if os.name != 'nt' else 'cls')

    # Display ASCII banner
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

    # Display system information
    try:
        from src.common.utils.system_info import format_system_info
        from src.version import VERSION, CHANNEL
        from src.common.config.manager import ConfigManager

        # Lấy kênh từ config.json với giá trị mặc định từ version.py
        config = ConfigManager()
        user_channel = config.get("core.channel", CHANNEL)

        # Đảm bảo giá trị channel hợp lệ
        if not user_channel or user_channel not in ["stable", "nightly", "dev"]:
            user_channel = CHANNEL

        sys_info = format_system_info()

        # Create a nice formatted box with system information
        console.print("╔════════════════════════════════════════════════════════════════════════════╗", style="bright_blue")
        console.print(f"║ [cyan]CPU:[/cyan] {sys_info['cpu']}".ljust(83) + "║", style="bright_blue")
        console.print(f"║ [cyan]RAM:[/cyan] {sys_info['ram']}".ljust(83) + "║", style="bright_blue")
        console.print(f"║ [cyan]Phiên bản:[/cyan] {VERSION} ([green]{user_channel}[/green])".ljust(83) + "║", style="bright_blue")
        console.print("╚════════════════════════════════════════════════════════════════════════════╝", style="bright_blue")
    except Exception as e:
        debug(f"Không thể hiển thị thông tin hệ thống: {str(e)}")


def not_implemented() -> None:
    """Handle not implemented features."""
    error("🚧 Feature not implemented yet")
    input("Press Enter to continue...")


def handle_website_menu() -> None:
    """Handle website management menu."""
    try:
        # Use prompt_menu module
        from src.features.website.prompts.prompt_menu import prompt_website_menu
        prompt_website_menu()
    except Exception as e:
        error(f"Error importing website menu: {e}")
        input("Press Enter to continue...")


def handle_ssl_menu() -> None:
    """Handle SSL certificates menu."""
    try:
        # Use prompt_menu module
        from src.features.ssl.prompts.prompt_menu import prompt_ssl_menu
        prompt_ssl_menu()
    except Exception as e:
        error(f"Error importing SSL menu: {e}")
        input("Press Enter to continue...")


def handle_cron_menu() -> None:
    """Handle cron job management menu."""
    try:
        # Use prompt_menu module
        from src.features.cron.prompts.prompt_menu import prompt_cron_menu
        prompt_cron_menu()
    except Exception as e:
        error(f"Error importing cron menu: {e}")
        input("Press Enter to continue...")


def handle_system_menu() -> None:
    """Handle system tools menu."""
    try:
        # Use prompt_menu module
        from src.features.system.prompts.prompt_menu import prompt_system_menu
        prompt_system_menu()
    except Exception as e:
        error(f"Error importing system menu: {e}")
        input("Press Enter to continue...")


def handle_cloud_menu() -> None:
    """Handle cloud storage menu."""
    try:
        # Use prompt_menu module
        from src.features.rclone.prompts.prompt_menu import prompt_rclone_menu
        prompt_rclone_menu()
    except Exception as e:
        error(f"Error importing rclone menu: {e}")
        input("Press Enter to continue...")


def handle_cloud_backup() -> None:
    """Handle cloud backup menu."""
    try:
        # Use prompt_menu module
        from src.features.backup.prompts.prompt_menu import prompt_cloud_backup
        prompt_cloud_backup()
    except Exception as e:
        error(f"Error importing cloud backup menu: {e}")
        input("Press Enter to continue...")


def handle_backup_menu() -> None:
    """Handle backup and restore menu."""
    try:
        # Use prompt_menu module
        from src.features.backup.prompts.prompt_menu import prompt_backup_menu
        prompt_backup_menu()
    except Exception as e:
        error(f"Error importing backup menu: {e}")
        input("Press Enter to continue...")


def handle_wordpress_menu() -> None:
    """Handle WordPress tools menu."""
    try:
        # Use prompt_menu module
        from src.features.wordpress.prompts.prompt_menu import prompt_wordpress_menu
        prompt_wordpress_menu()
    except Exception as e:
        error(f"Error importing WordPress menu: {e}")
        input("Press Enter to continue...")


def handle_wp_cache_menu() -> None:
    """Handle WP cache setup menu."""
    try:
        # Use prompt_menu module
        from src.features.cache.prompts.prompt_menu import prompt_cache_menu
        prompt_cache_menu()
    except Exception as e:
        error(f"Error importing cache menu: {e}")
        input("Press Enter to continue...")


def handle_php_menu() -> None:
    """Handle PHP management menu."""
    try:
        # Use prompt_menu module
        from src.features.php.prompts.prompt_menu import prompt_php_menu
        prompt_php_menu()
    except Exception as e:
        error(f"Error importing PHP menu: {e}")
        input("Press Enter to continue...")


def handle_mysql_menu() -> None:
    """Handle MySQL management menu."""
    try:
        # Use prompt_menu module
        from src.features.mysql.prompts.prompt_menu import prompt_mysql_menu
        prompt_mysql_menu()
    except Exception as e:
        error(f"Error importing MySQL menu: {e}")
        input("Press Enter to continue...")


def handle_update_menu() -> None:
    """Handle update menu."""
    try:
        # Use prompt_menu module
        from src.features.update.prompts.prompt_menu import prompt_update_menu
        prompt_update_menu()
    except Exception as e:
        error(f"Error importing update menu: {e}")
        input("Press Enter to continue...")


def show_main_menu() -> bool:
    """Show the main menu and handle selection. Returns False to exit."""
    # Display banner
    display_banner()

    # Create menu choices
    choices = [
        {"name": "1. Website Management", "value": "1"},
        {"name": "2. SSL Certificates", "value": "2"},
        {"name": "3. System Tools", "value": "3"},
        {"name": "4. RClone Management", "value": "4"},
        {"name": "5. WordPress Tools", "value": "5"},
        {"name": "6. Backup Management", "value": "6"},
        {"name": "7. WP Cache Setup", "value": "7"},
        {"name": "8. PHP Management", "value": "8"},
        {"name": "9. MySQL Management", "value": "9"},
        {"name": "10. Check & Update WP Docker", "value": "10"},
        {"name": "0. Exit", "value": "0"},
    ]

    # Show menu and get selection
    answer = questionary.select(
        "\n📋 Select a function:",
        choices=choices,
        style=custom_style
    ).ask()

    # Handle the selection
    if answer == "1":
        handle_website_menu()
    elif answer == "2":
        handle_ssl_menu()
    elif answer == "3":
        handle_system_menu()
    elif answer == "4":
        handle_cloud_menu()
    elif answer == "5":
        handle_wordpress_menu()
    elif answer == "6":
        handle_backup_menu()
    elif answer == "7":
        handle_wp_cache_menu()
    elif answer == "8":
        handle_php_menu()
    elif answer == "9":
        handle_mysql_menu()
    elif answer == "10":
        handle_update_menu()
    elif answer == "0":
        success("Exiting WP Docker. Goodbye!")
        return False

    return True


def main() -> None:
    """
    Main entry point for the application.

    This function:
    1. Loads the core environment using the CoreLoader
    2. Initializes the system using the BootstrapController
    3. Starts the main menu
    """
    # Enable exception hook for better error handling
    enable_exception_hook()

    # Step 1: Load core environment
    if not load_core():
        error("Failed to load core environment")
        sys.exit(1)

    # Load required environment variables
    env_required([
        "DEBUG_MODE",
        "INSTALL_DIR",
        "CONFIG_DIR",
        "TEMPLATES_DIR",
        "BASH_UTILS_DIR",
        "SRC_DIR",
        "SITES_DIR",
        "DATA_DIR"
    ])

    # Log startup information
    info("Starting WP Docker")
    debug(f"Install directory: {env['INSTALL_DIR']}")
    debug(f"Debug mode: {env['DEBUG_MODE']}")

    # Step 2: Initialize the system (run bootstraps)
    if not initialize_system():
        error("System initialization failed")
        sys.exit(1)

    success("System initialized successfully")

    try:
        # Ensure all containers are running
        debug("Ensuring all containers are running...")
        try:
            from src.scripts.check_containers import check_and_restart_containers
            check_and_restart_containers()
        except Exception as e:
            debug(f"Failed to check containers: {e}")

        # Step 3: Start the main menu loop
        exit_requested = False

        # First-time menu display (before update check)
        continue_menu = show_main_menu()
        if not continue_menu:
            exit_requested = True

        # Main loop with update checking at the end of each cycle
        while not exit_requested:
            # Check for updates if enabled (at the end of the menu cycle)
            if not env.get("DISABLE_UPDATE_CHECK", False):
                debug("Checking for updates...")
                try:
                    from src.features.update.core.version_updater import prompt_update
                    prompt_update()
                except Exception as e:
                    debug(f"Failed to check for updates: {e}")

            # Show menu again
            continue_menu = show_main_menu()
            if not continue_menu:
                exit_requested = True

    except KeyboardInterrupt:
        info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        error(f"Error in main: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

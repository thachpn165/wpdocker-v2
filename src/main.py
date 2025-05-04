#!/usr/bin/env python3
"""
Main entry point for the WP Docker application.

This module provides the main entry point for the application,
initializing the environment and starting the menu system.
"""

import os
import sys
from typing import Optional, List, Dict, Any, Callable

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
    os.system('clear' if os.name != 'nt' else 'cls')
    
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


def not_implemented() -> None:
    """Handle not implemented features."""
    error("🚧 Feature not implemented yet")
    input("Press Enter to continue...")


def handle_website_menu() -> None:
    """Handle website management menu."""
    try:
        choices = [
            {"name": "1. Create Website", "value": "1"},
            {"name": "2. Delete Website", "value": "2"},
            {"name": "3. List Websites", "value": "3"},
            {"name": "4. Restart Website", "value": "4"},
            {"name": "5. View Website Logs", "value": "5"},
            {"name": "6. View Website Info", "value": "6"},
            {"name": "7. Migrate Data to WP Docker", "value": "7"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n🌐 Website Management:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "3":
            try:
                from src.features.website.cli.list import list_websites
                list_websites()
            except ImportError:
                not_implemented()
        elif answer != "0":
            not_implemented()
    except Exception as e:
        error(f"Error in website menu: {e}")
        input("Press Enter to continue...")


def handle_ssl_menu() -> None:
    """Handle SSL certificates menu."""
    try:
        choices = [
            {"name": "1. Create Self-Signed Certificate", "value": "1"},
            {"name": "2. Create Let's Encrypt Certificate", "value": "2"},
            {"name": "3. Install Custom Certificate", "value": "3"},
            {"name": "4. Check Certificate Info", "value": "4"},
            {"name": "5. Edit Current Certificate", "value": "5"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n🔒 SSL Certificate Management:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer != "0":
            not_implemented()
    except Exception as e:
        error(f"Error in SSL menu: {e}")
        input("Press Enter to continue...")


def handle_cron_menu() -> None:
    """Handle cron job management menu."""
    try:
        choices = [
            {"name": "1. List Tasks", "value": "1"},
            {"name": "2. Enable/Disable Task", "value": "2"},
            {"name": "3. Delete Task", "value": "3"},
            {"name": "4. Run Task Now", "value": "4"},
            {"name": "0. Back to System Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n⏱️ Scheduled Task Management:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer != "0":
            not_implemented()
    except Exception as e:
        error(f"Error in cron menu: {e}")
        input("Press Enter to continue...")


def handle_system_menu() -> None:
    """Handle system tools menu."""
    try:
        choices = [
            {"name": "1. Rebuild Core Containers", "value": "1"},
            {"name": "2. Update WP Docker Version", "value": "2"},
            {"name": "3. View System Information", "value": "3"},
            {"name": "4. Change Language", "value": "4"},
            {"name": "5. Change Version Channel", "value": "5"},
            {"name": "6. Clean Docker", "value": "6"},
            {"name": "7. Manage Scheduled Tasks", "value": "7"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n⚙️ System Tools:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "7":
            handle_cron_menu()
        elif answer != "0":
            not_implemented()
    except Exception as e:
        error(f"Error in system menu: {e}")
        input("Press Enter to continue...")


def handle_cloud_menu() -> None:
    """Handle cloud storage menu."""
    try:
        try:
            from src.features.rclone.prompts.rclone_prompt import prompt_rclone_menu
            prompt_rclone_menu()
        except ImportError:
            choices = [
                {"name": "1. Manage RClone", "value": "1"},
                {"name": "0. Back to Main Menu", "value": "0"},
            ]
            
            answer = questionary.select(
                "\n📦 RClone Management:",
                choices=choices,
                style=custom_style
            ).ask()
            
            if answer != "0":
                not_implemented()
    except Exception as e:
        error(f"Error in cloud menu: {e}")
        input("Press Enter to continue...")


def handle_cloud_backup() -> None:
    """Handle cloud backup menu."""
    try:
        from src.features.backup.prompts.prompt_cloud_backup import prompt_cloud_backup
        prompt_cloud_backup()
    except ImportError:
        error("Cloud backup not implemented yet")
        input("Press Enter to continue...")


def handle_backup_menu() -> None:
    """Handle backup and restore menu."""
    try:
        try:
            from src.features.backup.prompts.prompt_backup_website import prompt_backup_website
            
            choices = [
                {"name": "1. Create Website Backup", "value": "1"},
                {"name": "2. Restore Backup", "value": "2"},
                {"name": "3. List Backups", "value": "3"},
                {"name": "4. Delete Backup", "value": "4"},
                {"name": "5. Schedule Automatic Backup", "value": "5"},
                {"name": "6. Cloud Backup with RClone", "value": "6"},
                {"name": "0. Back to Main Menu", "value": "0"},
            ]
            
            answer = questionary.select(
                "\n💾 Backup Management:",
                choices=choices,
                style=custom_style
            ).ask()
            
            if answer == "1":
                prompt_backup_website()
            elif answer == "6":
                handle_cloud_backup()
            elif answer != "0":
                not_implemented()
        except ImportError:
            error("Backup module not fully implemented yet")
            input("Press Enter to continue...")
    except Exception as e:
        error(f"Error in backup menu: {e}")
        input("Press Enter to continue...")


def handle_wordpress_menu() -> None:
    """Handle WordPress tools menu."""
    choices = [
        {"name": "1. Install WordPress", "value": "1"},
        {"name": "2. Manage Plugins", "value": "2"},
        {"name": "3. Manage Themes", "value": "3"},
        {"name": "4. Change WordPress Settings", "value": "4"},
        {"name": "0. Back to Main Menu", "value": "0"},
    ]
    
    answer = questionary.select(
        "\n🔌 WordPress Tools:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if answer != "0":
        not_implemented()


def handle_wp_cache_menu() -> None:
    """Handle WP cache setup menu."""
    choices = [
        {"name": "1. Install W3 Total Cache", "value": "1"},
        {"name": "2. Install WP Fastest Cache", "value": "2"},
        {"name": "3. Install WP Super Cache", "value": "3"},
        {"name": "4. Configure FastCGI Cache", "value": "4"},
        {"name": "0. Back to Main Menu", "value": "0"},
    ]
    
    answer = questionary.select(
        "\n⚡ WP Cache Setup:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if answer != "0":
        not_implemented()


def handle_php_menu() -> None:
    """Handle PHP management menu."""
    choices = [
        {"name": "1. Change PHP Version", "value": "1"},
        {"name": "2. Edit PHP Configuration", "value": "2"},
        {"name": "3. Install PHP Extension", "value": "3"},
        {"name": "0. Back to Main Menu", "value": "0"},
    ]
    
    answer = questionary.select(
        "\n🐘 PHP Management:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if answer != "0":
        not_implemented()


def handle_mysql_menu() -> None:
    """Handle MySQL management menu."""
    choices = [
        {"name": "1. Edit MySQL Configuration", "value": "1"},
        {"name": "2. Restore Database", "value": "2"},
        {"name": "0. Back to Main Menu", "value": "0"},
    ]
    
    answer = questionary.select(
        "\n🗄️ MySQL Management:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if answer != "0":
        not_implemented()


def handle_update_menu() -> None:
    """Handle update menu."""
    choices = [
        {"name": "1. Check for Updates", "value": "1"},
        {"name": "2. Update to Latest Version", "value": "2"},
        {"name": "3. View Changelog", "value": "3"},
        {"name": "0. Back to Main Menu", "value": "0"},
    ]
    
    answer = questionary.select(
        "\n🔄 Check & Update WP Docker:",
        choices=choices,
        style=custom_style
    ).ask()
    
    if answer != "0":
        not_implemented()


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
    info(f"Starting WP Docker")
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
            from scripts.check_containers import check_and_restart_containers
            check_and_restart_containers()
        except Exception as e:
            debug(f"Failed to check containers: {e}")
        
        # Step 3: Start the main menu loop
        exit_requested = False
        while not exit_requested:
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
"""
System tools menu prompt module.

This module provides the user interface for system management functions
like rebuilding containers, updating versions, and viewing system information.
"""

import questionary
from questionary import Style
from typing import Optional

from src.common.logging import info, error, debug, success
from src.features.system.prompts.prompt_container import prompt_container_menu
from src.features.system.prompts.prompt_system import (
    prompt_view_system_info,
    prompt_clean_docker,
    prompt_update_wpdocker,
    prompt_rebuild_containers,
    not_implemented
)

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

def prompt_system_menu() -> None:
    """Display system tools menu and handle user selection."""
    try:
        choices = [
            {"name": "1. Rebuild Core Containers", "value": "1"},
            {"name": "2. Update WP Docker Version", "value": "2"},
            {"name": "3. View System Information", "value": "3"},
            {"name": "4. Change Language", "value": "4"},
            {"name": "5. Change Version Channel", "value": "5"},
            {"name": "6. Clean Docker", "value": "6"},
            {"name": "7. Manage Scheduled Tasks", "value": "7"},
            {"name": "8. NGINX Web Server", "value": "8"},
            {"name": "9. Container Management", "value": "9"},
            {"name": "0. Back to Main Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n⚙️ System Tools:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "0":
            return
        elif answer == "1":
            prompt_rebuild_containers()
        elif answer == "2":
            prompt_update_wpdocker()
        elif answer == "3":
            prompt_view_system_info()
        elif answer == "6":
            prompt_clean_docker()
        elif answer == "7":
            from src.features.cron.prompts.prompt_menu import prompt_cron_menu
            prompt_cron_menu()
        elif answer == "8":
            from src.features.nginx.prompts.prompt_menu import prompt_nginx_menu
            prompt_nginx_menu()
        elif answer == "9":
            prompt_container_menu()
        else:
            not_implemented()
    except Exception as e:
        error(f"Error in system menu: {e}")
        input("Press Enter to continue...")
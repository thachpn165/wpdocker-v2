"""
Container status prompt module.

This module provides the interactive menu interfaces for container management.
"""

import questionary
from questionary import Style
from typing import Optional, Dict, Any, List

from src.common.logging import info, error, debug, success
from src.features.system.cli.containers import (
    cli_check_container_status,
    cli_list_containers,
    cli_restart_container,
    cli_view_container_logs
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

def prompt_container_menu() -> None:
    """Display container management menu and handle user selection."""
    try:
        choices = [
            {"name": "1. View Container Status", "value": "1"},
            {"name": "2. List All Containers", "value": "2"},
            {"name": "3. Restart Container", "value": "3"},
            {"name": "4. View Container Logs", "value": "4"},
            {"name": "0. Back to System Menu", "value": "0"},
        ]
        
        answer = questionary.select(
            "\n🐳 Container Management:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if answer == "0":
            return
        elif answer == "1":
            prompt_check_container_status()
        elif answer == "2":
            prompt_list_containers()
        elif answer == "3":
            prompt_restart_container()
        elif answer == "4":
            prompt_view_container_logs()
    except Exception as e:
        error(f"Error in container menu: {e}")
        input("Press Enter to continue...")

def prompt_check_container_status() -> None:
    """Prompt to check container status."""
    try:
        # First list all containers to help user choose
        containers = cli_list_containers(interactive=False)
        
        choices = [{"name": "All System Containers", "value": ""}]
        for container in containers:
            name = container.get("Names", "unknown")
            choices.append({"name": name, "value": name})
        
        container_name = questionary.select(
            "Select container to check:",
            choices=choices,
            style=custom_style
        ).ask()
        
        # Check the selected container
        cli_check_container_status(container_name, interactive=True)
        
        input("\nPress Enter to continue...")
    except Exception as e:
        error(f"Error checking container status: {e}")
        input("Press Enter to continue...")

def prompt_list_containers() -> None:
    """Prompt to list containers."""
    try:
        show_all = questionary.confirm(
            "Show all containers? (No = show only system containers)",
            default=False,
            style=custom_style
        ).ask()
        
        cli_list_containers(show_all=show_all, interactive=True)
        
        input("\nPress Enter to continue...")
    except Exception as e:
        error(f"Error listing containers: {e}")
        input("Press Enter to continue...")

def prompt_restart_container() -> None:
    """Prompt to restart a container."""
    try:
        # First list all containers to help user choose
        containers = cli_list_containers(interactive=False)
        
        choices = []
        for container in containers:
            name = container.get("Names", "unknown")
            state = container.get("State", "unknown")
            choices.append({"name": f"{name} ({state})", "value": name})
        
        if not choices:
            error("No containers found")
            input("Press Enter to continue...")
            return
            
        container_name = questionary.select(
            "Select container to restart:",
            choices=choices,
            style=custom_style
        ).ask()
        
        # Confirm before restarting
        confirmed = questionary.confirm(
            f"Are you sure you want to restart {container_name}?",
            default=False,
            style=custom_style
        ).ask()
        
        if confirmed:
            cli_restart_container(container_name, interactive=True)
        else:
            info("Restart cancelled")
            
        input("\nPress Enter to continue...")
    except Exception as e:
        error(f"Error restarting container: {e}")
        input("Press Enter to continue...")

def prompt_view_container_logs() -> None:
    """Prompt to view container logs."""
    try:
        # First list all containers to help user choose
        containers = cli_list_containers(interactive=False)
        
        choices = []
        for container in containers:
            name = container.get("Names", "unknown")
            state = container.get("State", "unknown")
            choices.append({"name": f"{name} ({state})", "value": name})
        
        if not choices:
            error("No containers found")
            input("Press Enter to continue...")
            return
            
        container_name = questionary.select(
            "Select container to view logs:",
            choices=choices,
            style=custom_style
        ).ask()
        
        # Ask for number of lines
        tail = questionary.text(
            "Number of log lines to display:",
            default="100",
            validate=lambda text: text.isdigit() and int(text) > 0,
            style=custom_style
        ).ask()
        
        cli_view_container_logs(container_name, int(tail), interactive=True)
        
        input("\nPress Enter to continue...")
    except Exception as e:
        error(f"Error viewing container logs: {e}")
        input("Press Enter to continue...")
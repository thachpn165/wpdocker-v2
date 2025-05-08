"""
Container management CLI module.

This module provides CLI commands for managing Docker containers.
"""

import click
import json
from typing import Dict, List, Optional, Any
from tabulate import tabulate

from src.common.logging import info, error, debug, success
from src.features.system.container_status import (
    get_container_status,
    get_all_containers,
    check_system_health,
    restart_container,
    get_container_logs
)

@click.group(name="container")
def container_cli():
    """Container management commands."""
    pass

@container_cli.command("status")
@click.argument("container_name", required=False)
@click.option("--interactive", is_flag=True, default=False, help="Run in interactive mode")
def container_status(container_name: Optional[str] = None, interactive: bool = False):
    """
    Check status of containers.
    
    If container_name is provided, show detailed status for that container.
    Otherwise, show status of all system containers.
    """
    return cli_check_container_status(container_name, interactive)

@container_cli.command("list")
@click.option("--all", "show_all", is_flag=True, default=False, help="Show all containers, including non-system containers")
@click.option("--interactive", is_flag=True, default=False, help="Run in interactive mode")
def list_containers(show_all: bool = False, interactive: bool = False):
    """List Docker containers status."""
    return cli_list_containers(show_all, interactive)

@container_cli.command("restart")
@click.argument("container_name", required=True)
@click.option("--interactive", is_flag=True, default=False, help="Run in interactive mode")
def container_restart(container_name: str, interactive: bool = False):
    """Restart a specific container."""
    return cli_restart_container(container_name, interactive)

@container_cli.command("logs")
@click.argument("container_name", required=True)
@click.option("--tail", type=int, default=100, help="Number of lines to show from the end of logs")
@click.option("--interactive", is_flag=True, default=False, help="Run in interactive mode")
def container_logs(container_name: str, tail: int = 100, interactive: bool = False):
    """View logs for a specific container."""
    return cli_view_container_logs(container_name, tail, interactive)

def cli_check_container_status(
    container_name: Optional[str] = None, 
    interactive: bool = True
) -> bool:
    """
    Check and display container status.
    
    Args:
        container_name: Optional name of container to check
        interactive: Whether to run in interactive mode
        
    Returns:
        True if healthy/successful, False otherwise
    """
    try:
        if container_name:
            # Check specific container
            status = get_container_status(container_name)
            
            if not status:
                error(f"Container '{container_name}' not found")
                return False
                
            if interactive:
                # Format for display
                table_data = []
                for key, value in status.items():
                    if key not in ['ports', 'networks', 'state']:  # Skip complex nested objects
                        table_data.append([key, str(value)])
                        
                click.echo(f"\n📊 Status for container: {container_name}")
                click.echo(tabulate(table_data, headers=["Property", "Value"], tablefmt="grid"))
                
                # Show health status with color
                is_healthy = status.get('running', False)
                health_status = status.get('health', 'none')
                
                if health_status != 'none':
                    is_healthy = health_status == 'healthy'
                    
                if is_healthy:
                    success("✅ Container is healthy")
                else:
                    error("❌ Container is not healthy")
                    
                return is_healthy
            else:
                # Return raw status data for non-interactive mode
                if status.get('running', False):
                    return True
                return False
        else:
            # Check all system containers
            all_healthy, status_map = check_system_health()
            
            if interactive:
                click.echo("\n📊 System Container Status:")
                
                table_data = []
                for name, data in status_map.items():
                    status_text = "✅ Healthy" if data['healthy'] else "❌ Unhealthy"
                    status_details = f"{data['status']}"
                    if data['health'] != 'none':
                        status_details += f", health: {data['health']}"
                        
                    table_data.append([name, status_text, status_details])
                
                click.echo(tabulate(table_data, headers=["Container", "Status", "Details"], tablefmt="grid"))
                
                if all_healthy:
                    success("\n✅ All system containers are healthy")
                else:
                    error("\n❌ Some system containers are not healthy")
                    
                return all_healthy
            else:
                # Return the boolean health status for non-interactive mode
                return all_healthy
    except Exception as e:
        error(f"Error checking container status: {e}")
        return False

def cli_list_containers(show_all: bool = False, interactive: bool = True) -> List[Dict[str, Any]]:
    """
    List all Docker containers.
    
    Args:
        show_all: Whether to show all containers or just system containers
        interactive: Whether to run in interactive mode
        
    Returns:
        List of container dictionaries
    """
    try:
        containers = get_all_containers()
        
        if not show_all:
            # Filter to show only system containers
            system_containers = ["nginx", "php", "mysql", "redis", "phpmyadmin", "wpcli", "rclone"]
            containers = [c for c in containers if any(sc in c.get("Names", "") for sc in system_containers)]
        
        if interactive:
            if not containers:
                info("No containers found")
                return []
                
            table_data = []
            for container in containers:
                name = container.get("Names", "unknown")
                image = container.get("Image", "unknown")
                status = container.get("State", "unknown")
                status_color = "✅" if status == "running" else "❌"
                ports = container.get("Ports", "")
                
                table_data.append([name, image, f"{status_color} {status}", ports])
            
            click.echo("\n🐳 Docker Containers:")
            click.echo(tabulate(table_data, headers=["Name", "Image", "Status", "Ports"], tablefmt="grid"))
            
        return containers
    except Exception as e:
        error(f"Error listing containers: {e}")
        return []

def cli_restart_container(container_name: str, interactive: bool = True) -> bool:
    """
    Restart a Docker container.
    
    Args:
        container_name: Name of container to restart
        interactive: Whether to run in interactive mode
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if interactive:
            info(f"Restarting container: {container_name}...")
            
        success = restart_container(container_name)
        
        if interactive:
            if success:
                success(f"✅ Container {container_name} restarted successfully")
            else:
                error(f"❌ Failed to restart container {container_name}")
                
        return success
    except Exception as e:
        error(f"Error restarting container: {e}")
        return False

def cli_view_container_logs(container_name: str, tail: int = 100, interactive: bool = True) -> str:
    """
    View logs for a specific container.
    
    Args:
        container_name: Name of container
        tail: Number of lines to show from the end
        interactive: Whether to run in interactive mode
        
    Returns:
        Log content as string
    """
    try:
        logs = get_container_logs(container_name, tail)
        
        if interactive:
            click.echo(f"\n📃 Logs for {container_name} (last {tail} lines):\n")
            click.echo(logs)
            
        return logs
    except Exception as e:
        error(f"Error viewing logs: {e}")
        return f"Error: {str(e)}"
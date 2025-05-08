"""
Container status utility module.

This module provides functions to check the status of various Docker containers
used in the wpdocker system, display their health, and provide diagnostics.
"""

import subprocess
import json
from typing import Dict, List, Tuple, Optional, Any

from src.common.logging import debug, info, error, success
from src.common.utils.environment import env
from src.common.debug import Debug


class ContainerStatus:
    """Class for managing and checking container statuses."""
    
    def __init__(self):
        """Initialize the ContainerStatus class."""
        self.debug = Debug("ContainerStatus")
    
    def get_all_containers(self) -> List[Dict[str, Any]]:
        """
        Get information about all containers.
        
        Returns:
            List of dictionaries with container information.
        """
        try:
            self.debug.print("Getting all containers...")
            
            # Using docker CLI to get all containers in JSON format
            cmd = ["docker", "ps", "-a", "--format", "{{json .}}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse the output (each line is a separate JSON object)
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    containers.append(json.loads(line))
                    
            return containers
        except subprocess.CalledProcessError as e:
            error(f"Error getting containers: {e}")
            return []
        except Exception as e:
            error(f"Unexpected error getting containers: {e}")
            return []
    
    def get_container_status(self, container_name: str) -> Dict[str, Any]:
        """
        Get the status of a specific container.
        
        Args:
            container_name: Name of the container to check
            
        Returns:
            Dictionary with container status information or empty dict if not found
        """
        try:
            self.debug.print(f"Getting status for container: {container_name}")
            
            # Using docker CLI to get container info in JSON format
            cmd = ["docker", "inspect", container_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse the output
            container_data = json.loads(result.stdout)
            if not container_data:
                return {}
            
            # Extract relevant information
            container_info = container_data[0]
            status_info = {
                "name": container_info.get("Name", "").lstrip('/'),
                "state": container_info.get("State", {}),
                "status": container_info.get("State", {}).get("Status", "unknown"),
                "running": container_info.get("State", {}).get("Running", False),
                "health": container_info.get("State", {}).get("Health", {}).get("Status", "none"),
                "image": container_info.get("Config", {}).get("Image", ""),
                "created": container_info.get("Created", ""),
                "ports": container_info.get("NetworkSettings", {}).get("Ports", {}),
                "networks": container_info.get("NetworkSettings", {}).get("Networks", {})
            }
            
            return status_info
        except subprocess.CalledProcessError:
            # Container likely doesn't exist
            return {}
        except Exception as e:
            error(f"Error getting status for {container_name}: {e}")
            return {}
    
    def get_container_logs(self, container_name: str, tail: int = 100) -> str:
        """
        Get logs from a specific container.
        
        Args:
            container_name: Name of the container
            tail: Number of lines to include (defaults to last 100)
            
        Returns:
            Container logs as a string
        """
        try:
            cmd = ["docker", "logs", f"--tail={tail}", container_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            error(f"Error getting logs for {container_name}: {e}")
            return f"Error retrieving logs: {e}"
        except Exception as e:
            error(f"Unexpected error getting logs: {e}")
            return f"Unexpected error: {e}"
    
    def restart_container(self, container_name: str) -> bool:
        """
        Restart a specific container.
        
        Args:
            container_name: Name of the container to restart
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = ["docker", "restart", container_name]
            subprocess.run(cmd, check=True, capture_output=True)
            success(f"Container {container_name} restarted successfully")
            return True
        except subprocess.CalledProcessError as e:
            error(f"Failed to restart {container_name}: {e}")
            return False
        except Exception as e:
            error(f"Unexpected error restarting container: {e}")
            return False
    
    def get_system_containers(self) -> List[Dict[str, Any]]:
        """
        Get status of all system-related containers.
        
        Returns:
            List of dictionaries with system container status information
        """
        # These are the core service containers
        system_containers = [
            "nginx", "php", "mysql", "redis", 
            "phpmyadmin", "wpcli", "rclone"
        ]
        
        result = []
        for container in system_containers:
            # For actual deployment the container names might have prefixes/suffixes
            # This logic searches for containers with these names in them
            all_containers = self.get_all_containers()
            matching = [c for c in all_containers if container in c.get("Names", "")]
            
            for match in matching:
                status = self.get_container_status(match.get("Names", ""))
                if status:
                    result.append(status)
        
        return result
    
    def check_system_health(self) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
        """
        Check the health of all system containers.
        
        Returns:
            Tuple with:
            - Boolean indicating if all containers are healthy
            - Dictionary of container statuses
        """
        containers = self.get_system_containers()
        
        status_map = {}
        all_healthy = True
        
        for container in containers:
            name = container.get("name", "unknown")
            is_healthy = container.get("running", False)
            
            # For containers with health checks, use the health status
            if container.get("health", "none") != "none":
                is_healthy = container.get("health", "") == "healthy"
            
            status_map[name] = {
                "healthy": is_healthy,
                "status": container.get("status", "unknown"),
                "health": container.get("health", "none"),
                "details": container
            }
            
            if not is_healthy:
                all_healthy = False
        
        return all_healthy, status_map


# Singleton instance
container_status = ContainerStatus()

def get_container_status(container_name: str) -> Dict[str, Any]:
    """
    Get status for a specific container.
    
    Args:
        container_name: Name of the container
        
    Returns:
        Dictionary with container status info
    """
    return container_status.get_container_status(container_name)

def get_all_containers() -> List[Dict[str, Any]]:
    """
    Get all containers on the system.
    
    Returns:
        List of container information dictionaries
    """
    return container_status.get_all_containers()

def check_system_health() -> Tuple[bool, Dict[str, Dict[str, Any]]]:
    """
    Check if all system containers are healthy.
    
    Returns:
        Tuple with:
        - Boolean indicating if all containers are healthy
        - Dictionary of container statuses
    """
    return container_status.check_system_health()

def restart_container(container_name: str) -> bool:
    """
    Restart a container.
    
    Args:
        container_name: Name of the container to restart
        
    Returns:
        True if successful, False otherwise
    """
    return container_status.restart_container(container_name)

def get_container_logs(container_name: str, tail: int = 100) -> str:
    """
    Get logs from a container.
    
    Args:
        container_name: Name of the container
        tail: Number of lines to include (defaults to last 100)
        
    Returns:
        Container logs as a string
    """
    return container_status.get_container_logs(container_name, tail)
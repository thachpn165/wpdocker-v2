#!/usr/bin/env python3
"""
Container checking and restarting script.

This script checks the status of all required Docker containers
and restarts them if they are not running.
"""

import os
import sys
import subprocess
from typing import List, Dict, Any
from src.common.logging import info, error, success, debug
from src.common.webserver.utils import get_current_webserver
# Add the project root to the sys path to allow imports
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

try:
    from src.common.logging import info, error, success, debug
    from src.common.utils.environment import env, load_environment
    from src.core.containers.compose import Compose
except ImportError as e:
    error(f"Error importing project modules: {e}")
    info("Make sure you're running this script from the project root directory")
    sys.exit(1)

# Container names to check
CONTAINERS = [
    "MYSQL_CONTAINER_NAME",
    # Webserver container sẽ được thêm động phía dưới
    "REDIS_CONTAINER_NAME",
    "WPCLI_CONTAINER_NAME",
    "RCLONE_CONTAINER_NAME"
]

# Thêm container webserver động vào CONTAINERS
try:
    webserver = get_current_webserver()
    webserver_env_var = f"{webserver.upper()}_CONTAINER_NAME"
    if webserver_env_var not in CONTAINERS:
        CONTAINERS.insert(1, webserver_env_var)
except Exception as e:
    error(f"Could not determine webserver: {e}")

def check_and_restart_containers() -> bool:
    """
    Check the status of all required containers and restart them if needed.
    
    Returns:
        bool: True if all containers are now running, False otherwise
    """
    # Load environment if not already loaded
    if not env:
        # Find core.env file
        project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        env_file = os.path.join(project_root, "core.env")
        if not os.path.exists(env_file):
            info(f"Environment file not found: {env_file}")
            return False
            
        # Load environment variables
        load_environment(env_file)
        
    info("Checking container status...")
    
    running_containers = get_running_containers()
    stopped_containers = get_stopped_containers()
    
    all_running = True
    for container_var in CONTAINERS:
        container_name = env.get(container_var)
        if not container_name:
            error(f"Container environment variable not set: {container_var}")
            continue
            
        if container_name in running_containers:
            info(f"✅ Container {container_name} is running")
        elif container_name in stopped_containers:
            info(f"🔄 Container {container_name} is stopped, restarting...")
            if restart_container(container_name):
                success(f"Container {container_name} restarted successfully")
            else:
                error(f"Failed to restart container {container_name}")
                all_running = False
        else:
            info(f"🔄 Container {container_name} does not exist, creating...")
            if create_container(container_name):
                success(f"Container {container_name} created and started successfully")
            else:
                error(f"Failed to create container {container_name}")
                all_running = False
                
    return all_running
    
def get_running_containers() -> List[str]:
    """
    Get a list of running container names.
    
    Returns:
        List[str]: Names of running containers
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except Exception as e:
        error(f"Failed to get running containers: {e}")
        return []
        
def get_stopped_containers() -> List[str]:
    """
    Get a list of stopped container names.
    
    Returns:
        List[str]: Names of stopped containers
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "status=exited", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except Exception as e:
        error(f"Failed to get stopped containers: {e}")
        return []
        
def restart_container(container_name: str) -> bool:
    """
    Restart a Docker container.
    
    Args:
        container_name: Name of the container to restart
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        subprocess.run(
            ["docker", "start", container_name],
            check=True, stdout=subprocess.DEVNULL
        )
        return True
    except Exception as e:
        error(f"Failed to restart container {container_name}: {e}")
        return False
        
def create_container(container_name: str) -> bool:
    """
    Create and start a container using its compose file.
    
    Args:
        container_name: Name of the container to create
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Determine which compose file to use based on container name
        if container_name == env.get("MYSQL_CONTAINER_NAME"):
            template = "mysql"
        elif container_name == env.get(webserver_env_var):
            template = webserver
        elif container_name == env.get("REDIS_CONTAINER_NAME"):
            template = "redis"
        elif container_name == env.get("WPCLI_CONTAINER_NAME"):
            template = "wpcli"
        elif container_name == env.get("RCLONE_CONTAINER_NAME"):
            template = "rclone"
        else:
            error(f"Unknown container type: {container_name}")
            return False
            
        # Path to compose file
        compose_file = os.path.join(env.get("INSTALL_DIR", "."), "docker-compose", f"docker-compose.{template}.yml")
        
        if not os.path.exists(compose_file):
            error(f"Compose file not found: {compose_file}")
            return False
            
        # Create compose object
        compose = Compose(
            name=container_name,
            output_path=compose_file
        )
        
        # Start the container
        return compose.ensure_running()
    except Exception as e:
        error(f"Failed to create container {container_name}: {e}")
        return False
        
if __name__ == "__main__":
    success_msg = "✅ All containers are running" 
    error_msg = "❌ Some containers failed to start"
    
    info("\n🐳 Docker Container Check and Restart Utility 🐳\n")
    
    if check_and_restart_containers():
        success(f"\n{success_msg}\n")
        sys.exit(0)
    else:
        error(f"\n{error_msg}\n")
        sys.exit(1)
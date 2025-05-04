"""
NGINX manager provides functionality for controlling the NGINX web server.

This module offers functions to test configuration, reload, and restart the NGINX service
running in a Docker container.
"""
import os
from typing import Optional, Dict, Any, List, Union, Tuple, Set

from src.common.logging import info, debug, warn, error, log_call
from src.common.utils.environment import env
from src.core.containers.compose import Compose
from src.common.containers.container import Container

# Initialize NGINX compose object once
container_name = env.get("NGINX_CONTAINER_NAME")
install_dir = env.get("INSTALL_DIR")

if container_name and install_dir:
    docker_compose_file = os.path.join(install_dir, "docker-compose", "docker-compose.nginx.yml")
    compose_nginx = Compose(name=container_name, output_path=docker_compose_file)
else:
    compose_nginx = None


@log_call
def test_config() -> bool:
    """
    Test the NGINX configuration for syntax errors.
    
    Returns:
        bool: True if the configuration is valid, False otherwise.
    """
    if not compose_nginx:
        error("❌ NGINX container information not found.")
        return False
    
    try:
        container = Container(name=container_name)
        container.exec(["openresty", "-t"])
        info("✅ NGINX configuration is valid.")
        return True
    except Exception as e:
        error(f"❌ Error testing NGINX configuration: {e}")
        return False


@log_call 
def reload() -> bool:
    """
    Reload the NGINX configuration without restarting the container.
    
    This is useful for applying configuration changes without disrupting existing connections.
    
    Returns:
        bool: True if the reload was successful, False otherwise.
    """
    if not compose_nginx:
        error("❌ NGINX container information not found.")
        return False
    
    if not test_config():
        warn("⚠️ Skipping reload due to configuration errors.")
        return False
    
    try:
        container = Container(name=container_name)
        container.exec(["openresty", "-s", "reload"])
        info("🔄 NGINX reloaded successfully.")
        return True
    except Exception as e:
        error(f"❌ Error reloading NGINX: {e}")
        return False


@log_call
def restart() -> bool:
    """
    Restart the NGINX container.
    
    This completely stops and starts the container, which will interrupt all active connections.
    
    Returns:
        bool: True if the restart was successful, False otherwise.
    """
    if not compose_nginx:
        error("❌ NGINX container information not found.")
        return False
    
    if not os.path.isfile(compose_nginx.output_path):
        error(f"❌ Docker-compose file not found: {compose_nginx.output_path}")
        return False
    
    try:
        compose_nginx.down()
        compose_nginx.up(force_recreate=True)
        info("🔁 NGINX restarted successfully.")
        return True
    except Exception as e:
        error(f"❌ Error restarting NGINX: {e}")
        return False
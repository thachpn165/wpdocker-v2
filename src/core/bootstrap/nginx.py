"""
NGINX bootstrap module.

This module handles NGINX webserver initialization, configuration,
and container setup.
"""

import os
from typing import Dict, Any, List, Optional

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.core.bootstrap.base import BaseBootstrap
from src.core.containers.compose import Compose
from src.core.containers.container import Container


class NginxBootstrap(BaseBootstrap):
    """Handles NGINX initialization and configuration."""
    
    def __init__(self) -> None:
        """Initialize NGINX bootstrap."""
        super().__init__("NginxBootstrap")
        
    def is_bootstrapped(self) -> bool:
        """
        Check if NGINX is already bootstrapped.
        
        Returns:
            bool: True if NGINX is already bootstrapped, False otherwise
        """
        # Check if NGINX configuration exists in features directory
        nginx_conf_path = os.path.join(env["INSTALL_DIR"], "src/features/nginx/configs/nginx.conf")
        
        # Also check old location for compatibility
        old_nginx_conf_path = os.path.join(env["INSTALL_DIR"], "core/backend/modules/nginx/nginx.conf")
        
        if not os.path.exists(nginx_conf_path) and not os.path.exists(old_nginx_conf_path):
            return False
            
        # Check if NGINX compose file exists
        compose_path = os.path.join(env["INSTALL_DIR"], "docker-compose", "docker-compose.nginx.yml")
        if not os.path.exists(compose_path):
            return False
            
        return True
        
    def check_prerequisites(self) -> bool:
        """
        Check if prerequisites for NGINX bootstrap are met.
        
        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        required_env_vars = [
            "INSTALL_DIR",
            "PROJECT_NAME",
            "NGINX_CONTAINER_NAME",
            "NGINX_IMAGE_NAME",
            "DOCKER_NETWORK",
            "NGINX_CONTAINER_PATH",
            "NGINX_CONTAINER_CONF_PATH",
            "TEMPLATES_DIR"
        ]
        
        for var in required_env_vars:
            if var not in env:
                self.debug.error(f"Required environment variable not set: {var}")
                return False
                
        return True
        
    def execute_bootstrap(self) -> bool:
        """
        Execute the NGINX bootstrap process.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.debug.info("Initializing NGINX webserver...")
            
            # Step 1: Create nginx.conf if it doesn't exist
            if not self._create_nginx_conf():
                return False
                
            # Step 2: Create and start NGINX container
            if not self._create_nginx_container():
                return False
                
            # Step 3: Set proper permissions
            if not self._set_directory_permissions():
                return False
                
            self.debug.success("NGINX bootstrap completed successfully")
            return True
        except Exception as e:
            self.debug.error(f"Failed to bootstrap NGINX: {e}")
            return False
        
    def mark_bootstrapped(self) -> None:
        """Mark NGINX as bootstrapped."""
        # NGINX bootstrap is marked by the presence of its configuration files
        pass
        
    def _create_nginx_conf(self) -> bool:
        """
        Create nginx.conf from template if it doesn't exist.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use new structure location
            nginx_conf_dir = os.path.join(env["INSTALL_DIR"], "src/features/nginx/configs")
            nginx_conf_path = os.path.join(nginx_conf_dir, "nginx.conf")
            
            # Create directory if it doesn't exist
            os.makedirs(nginx_conf_dir, exist_ok=True)
            
            # Check if the file already exists
            if os.path.exists(nginx_conf_path):
                self.debug.debug(f"NGINX configuration already exists: {nginx_conf_path}")
                return True
                
            # Get template path from new structure
            nginx_conf_template = os.path.join(env["TEMPLATES_DIR"], "nginx", "nginx.conf.template")
            
            self.debug.debug(f"Creating NGINX configuration at: {nginx_conf_path}")
            
            with open(nginx_conf_template, "r") as f:
                content = f.read()
                
            # Replace placeholders with actual values
            content = content.replace("${NGINX_CONTAINER_PATH}", env["NGINX_CONTAINER_PATH"])
            content = content.replace("${NGINX_CONTAINER_CONF_PATH}", env["NGINX_CONTAINER_CONF_PATH"])
            
            with open(nginx_conf_path, "w") as f:
                f.write(content)
                
            self.debug.success(f"NGINX configuration created: {nginx_conf_path}")
            return True
        except Exception as e:
            self.debug.error(f"Failed to create NGINX configuration: {e}")
            return False
            
    def _create_nginx_container(self) -> bool:
        """
        Create and start NGINX container.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create docker-compose directory if it doesn't exist
            docker_compose_dir = os.path.join(env["INSTALL_DIR"], "docker-compose")
            os.makedirs(docker_compose_dir, exist_ok=True)
            
            # Initialize Compose object
            template_path = os.path.join(env["TEMPLATES_DIR"], "docker-compose", "docker-compose.nginx.yml.template")
            output_path = os.path.join(docker_compose_dir, "docker-compose.nginx.yml")
            
            compose = Compose(
                name=env["NGINX_CONTAINER_NAME"],
                template_path=template_path,
                output_path=output_path,
                env_map={
                    "INSTALL_DIR": env["INSTALL_DIR"],
                    "PROJECT_NAME": env["PROJECT_NAME"],
                    "NGINX_CONTAINER_NAME": env["NGINX_CONTAINER_NAME"],
                    "NGINX_IMAGE_NAME": env["NGINX_IMAGE_NAME"],
                    "DOCKER_NETWORK": env["DOCKER_NETWORK"],
                    "NGINX_CONTAINER_PATH": env["NGINX_CONTAINER_PATH"],
                    "NGINX_CONTAINER_CONF_PATH": env["NGINX_CONTAINER_CONF_PATH"]
                }
            )
            
            if not compose.ensure_ready():
                self.debug.error("Failed to create NGINX container")
                return False
                
            self.debug.success("NGINX container created and started")
            return True
        except Exception as e:
            self.debug.error(f"Failed to create NGINX container: {e}")
            return False
            
    def _set_directory_permissions(self) -> bool:
        """
        Set proper permissions on NGINX directories.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Initialize Container object to check and set permissions
            container = Container(name=env["NGINX_CONTAINER_NAME"])
            
            if not container.exists():
                self.debug.error("NGINX container does not exist")
                return False
                
            # List of directories to check permissions
            paths_to_check = [
                env["NGINX_CONTAINER_CONF_PATH"],
                "/var/www"
            ]
            
            # Set permissions
            for path in paths_to_check:
                container.exec(["chown", "-R", "www-data:www-data", path], user="root")
                self.debug.debug(f"Set ownership of {path} to www-data:www-data")
                
            return True
        except Exception as e:
            self.debug.error(f"Failed to set directory permissions: {e}")
            return False
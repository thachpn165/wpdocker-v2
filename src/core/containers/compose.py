"""
Docker Compose management.

This module provides the Compose class for managing Docker Compose services.
"""

import os
from typing import Dict, Optional, List, Any

from python_on_whales import DockerClient
from src.common.logging import Debug, log_call


class Compose:
    """Manages Docker Compose services and files."""
    
    def __init__(self, name: str, template_path: Optional[str] = None, 
                output_path: Optional[str] = None, env_map: Optional[Dict[str, str]] = None, 
                sensitive_env: Optional[Dict[str, str]] = None) -> None:
        """
        Initialize a Compose manager.
        
        Args:
            name: Service name
            template_path: Path to compose template file
            output_path: Path for generated compose file
            env_map: Environment variable mappings
            sensitive_env: Sensitive environment variables (not logged)
        """
        self.name = name
        self.template_path = template_path
        self.output_path = output_path
        self.env_map = env_map or {}
        self.sensitive_env = sensitive_env or {}
        self.debug = Debug("Compose")

        if self.output_path:
            self.docker = DockerClient(compose_files=[self.output_path])
        else:
            self.docker = DockerClient()

    def get_container(self):
        """
        Get the main container for this compose service.
        
        Returns:
            Container object or None if not found
        """
        containers = self.docker.container.list(all=True, filters={"name": self.name})
        return containers[0] if containers else None

    def exists(self) -> bool:
        """
        Check if the compose container exists.
        
        Returns:
            bool: True if container exists, False otherwise
        """
        return self.get_container() is not None

    def running(self) -> bool:
        """
        Check if the compose container is running.
        
        Returns:
            bool: True if container is running, False otherwise
        """
        container = self.get_container()
        return container is not None and container.state == "running"

    def not_running(self) -> bool:
        """
        Check if the compose container exists but is not running.
        
        Returns:
            bool: True if container exists but not running, False otherwise
        """
        container = self.get_container()
        return container is not None and container.state != "running"

    @log_call
    def generate_compose_file(self) -> bool:
        """
        Generate Docker Compose file from template.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.template_path, "r") as f:
                content = f.read()

            # Get environment variables from the environment
            from src.common.utils.environment import env

            # First, replace variables from env_map (passed in constructor)
            for key, value in self.env_map.items():
                content = content.replace(f"${{{key}}}", value)

            # Replace sensitive environment variables (passed in constructor)
            for key, value in self.sensitive_env.items():
                content = content.replace(f"${{{key}}}", value)
                
            # Then replace any remaining variables from the system environment
            # This ensures MYSQL_CONFIG_FILE and other env vars are correctly replaced
            for key, value in env.items():
                # Only replace if the variable still exists in the template
                # and we haven't already replaced it from env_map
                if f"${{{key}}}" in content and key not in self.env_map and key not in self.sensitive_env:
                    self.debug.debug(f"Using environment variable {key}={value}")
                    content = content.replace(f"${{{key}}}", value)

            with open(self.output_path, "w") as f:
                f.write(content)
                
            self.debug.info(f"Generated compose file: {self.output_path}")
            return True
        except Exception as e:
            self.debug.error(f"Failed to generate compose file: {e}")
            return False

    @log_call
    def up(self, detach: bool = True, force_recreate: bool = False, 
          no_build: bool = False) -> bool:
        """
        Start containers using docker-compose up.
        
        Args:
            detach: Run containers in background
            force_recreate: Force recreate containers
            no_build: Don't build images
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.docker.compose.up(
                detach=detach,
                force_recreate=force_recreate,
                no_build=no_build,
                remove_orphans=False,
                quiet=True
            )
            self.debug.info(f"Started service: {self.name}")
            return True
        except Exception as e:
            self.debug.error(f"Failed to start service {self.name}: {e}")
            return False

    @log_call
    def down(self) -> bool:
        """
        Stop and remove containers using docker-compose down.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.docker.compose.down()
            self.debug.info(f"Stopped service: {self.name}")
            return True
        except Exception as e:
            self.debug.error(f"Failed to stop service {self.name}: {e}")
            return False

    @log_call
    def restart(self) -> bool:
        """
        Restart containers.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.down()
            self.up(force_recreate=True)
            self.debug.info(f"Restarted service: {self.name}")
            return True
        except Exception as e:
            self.debug.error(f"Failed to restart service {self.name}: {e}")
            return False

    @log_call
    def ensure_running(self) -> bool:
        """
        Ensure the container is running, starting it if needed.
        
        Returns:
            bool: True if container is running, False otherwise
        """
        container = self.get_container()
        try:
            if container is None:
                self.debug.warn(f"Container {self.name} doesn't exist. Creating...")
                return self.up()
            elif container.state != "running":
                self.debug.warn(f"Container {self.name} is stopped. Starting...")
                self.docker.container.start(container)
                return True
            else:
                self.debug.info(f"Container {self.name} is already running")
                return True
        except Exception as e:
            self.debug.error(f"Failed to ensure {self.name} is running: {e}")
            return False

    @log_call
    def ensure_ready(self, auto_start: bool = True) -> bool:
        """
        Ensure compose file exists and container is ready to use.
        
        Args:
            auto_start: Whether to start the container if it's not running
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            compose_missing = not os.path.exists(self.output_path)
            container_missing = not self.exists()

            if compose_missing and self.template_path:
                self.debug.info(f"Generating compose file for {self.name}...")
                if not self.generate_compose_file():
                    return False

            if container_missing:
                self.debug.info(f"Creating container {self.name}...")
                if not self.up():
                    return False
            else:
                self.debug.debug(f"Container {self.name} already exists")

            if auto_start:
                return self.ensure_running()
            return True
        except Exception as e:
            self.debug.error(f"Failed to ensure {self.name} is ready: {e}")
            return False
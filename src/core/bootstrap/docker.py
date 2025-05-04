"""
Docker bootstrap module.

This module handles Docker initialization, network and volume creation,
and user permissions.
"""

import subprocess
import platform
import os
from typing import Optional, Dict, List, Any

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.core.bootstrap.base import BaseBootstrap
from src.features.docker.installer import install_docker_if_missing


class DockerBootstrap(BaseBootstrap):
    """Handles Docker initialization and configuration."""
    
    def __init__(self) -> None:
        """Initialize Docker bootstrap."""
        super().__init__("DockerBootstrap")
        
    def is_bootstrapped(self) -> bool:
        """
        Check if Docker is already bootstrapped.
        
        Returns:
            bool: True if Docker is already bootstrapped, False otherwise
        """
        # Docker is considered bootstrapped if it's running and the network exists
        if not self._is_docker_running():
            return False
            
        # Check if the network exists
        network = env.get("DOCKER_NETWORK")
        if not network:
            self.debug.error("DOCKER_NETWORK environment variable not set")
            return False
            
        result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{.Name}}"],
            capture_output=True, text=True
        )
        networks = result.stdout.strip().splitlines()
        
        return network in networks
        
    def check_prerequisites(self) -> bool:
        """
        Check if prerequisites for Docker bootstrap are met.
        
        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        # Check if DOCKER_NETWORK environment variable is set
        if "DOCKER_NETWORK" not in env:
            self.debug.error("DOCKER_NETWORK environment variable is required")
            return False
            
        return True
        
    def execute_bootstrap(self) -> bool:
        """
        Execute the Docker bootstrap process.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Step 1: Install Docker if missing
        if not install_docker_if_missing():
            self.debug.error("Docker installation failed")
            return False
            
        # Step 2: Verify Docker is running
        if not self._is_docker_running():
            self.debug.error("Docker is not running")
            return False
            
        # Step 3: Create Docker network
        if not self._create_docker_network():
            self.debug.error("Failed to create Docker network")
            return False
            
        # Step 4: Create FastCGI cache volume
        if not self._create_fastcgi_cache_volume():
            self.debug.error("Failed to create FastCGI cache volume")
            return False
            
        # Step 5: Add user to Docker group (Linux only)
        if platform.system() != "Darwin":
            if not self._add_user_to_docker_group():
                self.debug.warn("Could not add user to Docker group")
                # This is not a critical failure
                
        return True
        
    def mark_bootstrapped(self) -> None:
        """Mark Docker as bootstrapped."""
        # Docker bootstrap doesn't need explicit marking
        pass
        
    def _is_docker_running(self) -> bool:
        """
        Check if Docker is running.
        
        Returns:
            bool: True if Docker is running, False otherwise
        """
        try:
            subprocess.run(
                ["docker", "info"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.debug.info("Docker is installed and running")
            return True
        except Exception:
            self.debug.error("Docker is not installed or not running")
            return False
            
    def _create_docker_network(self) -> bool:
        """
        Create Docker network if it doesn't exist.
        
        Returns:
            bool: True if successful, False otherwise
        """
        network = env["DOCKER_NETWORK"]
        try:
            result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{.Name}}"],
                capture_output=True, text=True
            )
            networks = result.stdout.strip().splitlines()
            
            if network not in networks:
                subprocess.run(
                    ["docker", "network", "create", network],
                    check=True
                )
                self.debug.success(f"Created Docker network: {network}")
            else:
                self.debug.debug(f"Docker network already exists: {network}")
                
            return True
        except Exception as e:
            self.debug.error(f"Failed to create Docker network: {e}")
            return False
            
    def _create_fastcgi_cache_volume(self) -> bool:
        """
        Create FastCGI cache volume if it doesn't exist.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "volume", "ls", "--format", "{{.Name}}"],
                capture_output=True, text=True
            )
            volumes = result.stdout.strip().splitlines()
            volume_name = "wpdocker_fastcgi_cache_data"
            
            if volume_name not in volumes:
                subprocess.run(
                    ["docker", "volume", "create", volume_name],
                    check=True
                )
                self.debug.success(f"Created Docker volume: {volume_name}")
            else:
                self.debug.debug(f"Docker volume already exists: {volume_name}")
                
            return True
        except Exception as e:
            self.debug.error(f"Failed to create volume: {e}")
            return False
            
    def _add_user_to_docker_group(self) -> bool:
        """
        Add current user to Docker group (Linux only).
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            user = os.getenv("USER")
            if not user:
                self.debug.warn("USER environment variable not set")
                return False
                
            subprocess.run(
                ["sudo", "usermod", "-aG", "docker", user],
                check=True
            )
            self.debug.success(f"Added user '{user}' to 'docker' group (may require logout)")
            return True
        except Exception as e:
            self.debug.warn(f"Could not add user to docker group: {e}")
            return False
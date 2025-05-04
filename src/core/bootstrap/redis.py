"""
Redis bootstrap module.

This module handles Redis container initialization and configuration.
"""

import os
from typing import Dict, Any, Optional

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.core.bootstrap.base import BaseBootstrap
from src.core.containers.compose import Compose


class RedisBootstrap(BaseBootstrap):
    """Handles Redis initialization and configuration."""
    
    def __init__(self) -> None:
        """Initialize Redis bootstrap."""
        super().__init__("RedisBootstrap")
        
    def is_bootstrapped(self) -> bool:
        """
        Check if Redis is already bootstrapped.
        
        Returns:
            bool: True if Redis is already bootstrapped, False otherwise
        """
        # Check if Redis compose file exists
        compose_path = os.path.join(env["INSTALL_DIR"], "docker-compose", "docker-compose.redis.yml")
        if not os.path.exists(compose_path):
            return False
            
        return True
        
    def check_prerequisites(self) -> bool:
        """
        Check if prerequisites for Redis bootstrap are met.
        
        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        required_env_vars = [
            "INSTALL_DIR",
            "PROJECT_NAME",
            "REDIS_IMAGE",
            "REDIS_CONTAINER_NAME",
            "DOCKER_NETWORK",
            "TEMPLATES_DIR"
        ]
        
        for var in required_env_vars:
            if var not in env:
                self.debug.error(f"Required environment variable not set: {var}")
                return False
                
        return True
        
    def execute_bootstrap(self) -> bool:
        """
        Execute the Redis bootstrap process.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.debug.info("Initializing Redis container...")
            
            # Create docker-compose directory if it doesn't exist
            docker_compose_dir = os.path.join(env["INSTALL_DIR"], "docker-compose")
            os.makedirs(docker_compose_dir, exist_ok=True)
            
            # Create and start Redis container
            template_path = os.path.join(env["TEMPLATES_DIR"], "docker-compose", "docker-compose.redis.yml.template")
            output_path = os.path.join(docker_compose_dir, "docker-compose.redis.yml")
            
            compose = Compose(
                name=env["REDIS_CONTAINER_NAME"],
                template_path=template_path,
                output_path=output_path,
                env_map={
                    "PROJECT_NAME": env["PROJECT_NAME"],
                    "REDIS_IMAGE": env["REDIS_IMAGE"],
                    "REDIS_CONTAINER_NAME": env["REDIS_CONTAINER_NAME"],
                    "DOCKER_NETWORK": env["DOCKER_NETWORK"]
                }
            )
            
            if not compose.ensure_ready():
                self.debug.error("Failed to create Redis container")
                return False
                
            self.debug.success("Redis container created and started")
            return True
        except Exception as e:
            self.debug.error(f"Failed to bootstrap Redis: {e}")
            return False
        
    def mark_bootstrapped(self) -> None:
        """Mark Redis as bootstrapped."""
        # Redis bootstrap is marked by the presence of its compose file
        pass
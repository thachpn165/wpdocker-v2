"""
WordPress CLI bootstrap module.

This module handles WordPress CLI container initialization and configuration
for WordPress management through Docker.
"""

import os
import shutil
from typing import Dict, Any, Optional

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.core.bootstrap.base import BaseBootstrap
from src.core.containers.compose import Compose
from src.features.mysql.utils import get_mysql_root_password


class WPCLIBootstrap(BaseBootstrap):
    """Handles WordPress CLI initialization and configuration."""
    
    def __init__(self) -> None:
        """Initialize WordPress CLI bootstrap."""
        super().__init__("WPCLIBootstrap")
        
    def is_bootstrapped(self) -> bool:
        """
        Check if WordPress CLI is already bootstrapped.
        
        Returns:
            bool: True if WordPress CLI is already bootstrapped, False otherwise
        """
        # Check if WP-CLI configuration exists
        wpcli_ini_path = os.path.join(env["CONFIG_DIR"], "wpcli-custom.ini")
        if not os.path.exists(wpcli_ini_path):
            return False
            
        # Check if WP-CLI compose file exists
        compose_path = os.path.join(env["INSTALL_DIR"], "docker-compose", "docker-compose.wpcli.yml")
        if not os.path.exists(compose_path):
            return False
            
        return True
        
    def check_prerequisites(self) -> bool:
        """
        Check if prerequisites for WordPress CLI bootstrap are met.
        
        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        required_env_vars = [
            "PROJECT_NAME",
            "WPCLI_CONTAINER_NAME",
            "DOCKER_NETWORK",
            "INSTALL_DIR",
            "SITES_DIR",
            "MYSQL_CONTAINER_NAME",
            "CONFIG_DIR",
            "TEMPLATES_DIR"
        ]
        
        for var in required_env_vars:
            if var not in env:
                self.debug.error(f"Required environment variable not set: {var}")
                return False
                
        return True
        
    def execute_bootstrap(self) -> bool:
        """
        Execute the WordPress CLI bootstrap process.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.debug.info("Initializing WordPress CLI container...")
            
            # Step 1: Ensure WP-CLI PHP configuration exists
            if not self._setup_wpcli_config():
                return False
                
            # Step 2: Get MySQL root password
            mysql_root_pass = get_mysql_root_password()
            if not mysql_root_pass:
                self.debug.error("Failed to get MySQL root password")
                return False
                
            # Step 3: Create and start WordPress CLI container
            if not self._create_wpcli_container(mysql_root_pass):
                return False
                
            self.debug.success("WordPress CLI bootstrap completed successfully")
            return True
        except Exception as e:
            self.debug.error(f"Failed to bootstrap WordPress CLI: {e}")
            return False
        
    def mark_bootstrapped(self) -> None:
        """Mark WordPress CLI as bootstrapped."""
        # WordPress CLI bootstrap is marked by the presence of its configuration files
        pass
        
    def _setup_wpcli_config(self) -> bool:
        """
        Set up WordPress CLI PHP configuration.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            wpcli_ini_target = os.path.join(env["CONFIG_DIR"], "wpcli-custom.ini")
            wpcli_ini_template = os.path.join(env["TEMPLATES_DIR"], "wpcli", "wpcli-custom.ini")
            
            # Skip if configuration already exists
            if os.path.exists(wpcli_ini_target):
                self.debug.debug(f"WordPress CLI configuration already exists: {wpcli_ini_target}")
                return True
                
            # Ensure target directory exists
            os.makedirs(os.path.dirname(wpcli_ini_target), exist_ok=True)
            
            # Check if template exists
            if not os.path.exists(wpcli_ini_template):
                self.debug.error(f"WordPress CLI template not found: {wpcli_ini_template}")
                return False
                
            # Copy template to target location
            shutil.copy2(wpcli_ini_template, wpcli_ini_target)
            self.debug.info(f"WordPress CLI configuration created: {wpcli_ini_target}")
            
            return True
        except Exception as e:
            self.debug.error(f"Failed to set up WordPress CLI configuration: {e}")
            return False
            
    def _create_wpcli_container(self, mysql_root_pass: str) -> bool:
        """
        Create and start WordPress CLI container.
        
        Args:
            mysql_root_pass: MySQL root password
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create docker-compose directory if it doesn't exist
            docker_compose_dir = os.path.join(env["INSTALL_DIR"], "docker-compose")
            os.makedirs(docker_compose_dir, exist_ok=True)
            
            # Get paths for compose files
            template_path = os.path.join(env["TEMPLATES_DIR"], "docker-compose", "docker-compose.wpcli.yml.template")
            output_path = os.path.join(docker_compose_dir, "docker-compose.wpcli.yml")
            
            # Check if template exists
            if not os.path.exists(template_path):
                self.debug.error(f"WordPress CLI compose template not found: {template_path}")
                return False
                
            # Create compose instance and ensure container is running
            compose = Compose(
                name=env["WPCLI_CONTAINER_NAME"],
                template_path=template_path,
                output_path=output_path,
                env_map={
                    "PROJECT_NAME": env["PROJECT_NAME"],
                    "WPCLI_CONTAINER_NAME": env["WPCLI_CONTAINER_NAME"],
                    "DOCKER_NETWORK": env["DOCKER_NETWORK"],
                    "SITES_DIR": env["SITES_DIR"],
                    "MYSQL_CONTAINER_NAME": env["MYSQL_CONTAINER_NAME"],
                    "MYSQL_ROOT_PASSWORD": mysql_root_pass,
                    "CONFIG_DIR": env["CONFIG_DIR"],
                }
            )
            
            if not compose.ensure_ready():
                self.debug.error("Failed to create WordPress CLI container")
                return False
                
            self.debug.success(f"WordPress CLI container created: {env['WPCLI_CONTAINER_NAME']}")
            return True
        except Exception as e:
            self.debug.error(f"Failed to create WordPress CLI container: {e}")
            return False
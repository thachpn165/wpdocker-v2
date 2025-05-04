"""
MySQL bootstrap module.

This module handles MySQL container initialization, configuration,
and password management.
"""

import os
import questionary
from typing import Dict, Any, Optional

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.common.utils.system_info import get_total_ram_mb, get_total_cpu_cores
from src.common.utils.crypto import encrypt, decrypt
from src.common.utils.password import strong_password
from src.core.bootstrap.base import BaseBootstrap
from src.core.config.manager import ConfigManager
from src.core.containers.compose import Compose


class MySQLBootstrap(BaseBootstrap):
    """Handles MySQL initialization and configuration."""
    
    def __init__(self) -> None:
        """Initialize MySQL bootstrap."""
        super().__init__("MySQLBootstrap")
        self.config_manager = ConfigManager()
        
    def is_bootstrapped(self) -> bool:
        """
        Check if MySQL is already bootstrapped.
        
        Returns:
            bool: True if MySQL is already bootstrapped, False otherwise
        """
        # Check if MySQL configuration exists
        config_data = self.config_manager.get()
        if not config_data.get("mysql", {}).get("version"):
            return False
            
        if not config_data.get("mysql", {}).get("root_passwd"):
            return False
            
        # Check if MySQL config file exists
        config_path = os.path.join(env["CONFIG_DIR"], "mysql.conf")
        if not os.path.exists(config_path):
            return False
            
        # Check if MySQL compose file exists
        compose_path = os.path.join(env["INSTALL_DIR"], "docker-compose", "docker-compose.mysql.yml")
        if not os.path.exists(compose_path):
            return False
            
        return True
        
    def check_prerequisites(self) -> bool:
        """
        Check if prerequisites for MySQL bootstrap are met.
        
        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        required_env_vars = [
            "PROJECT_NAME",
            "MYSQL_CONTAINER_NAME",
            "MYSQL_VOLUME_NAME",
            "DOCKER_NETWORK",
            "INSTALL_DIR",
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
        Execute the MySQL bootstrap process.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get configuration details
            mysql_container = env["MYSQL_CONTAINER_NAME"]
            volume_name = env["MYSQL_VOLUME_NAME"]
            docker_network = env["DOCKER_NETWORK"]
            project_name = env["PROJECT_NAME"]
            
            # Step 1: Configure MySQL version
            if not self._configure_mysql_version():
                return False
                
            # Step 2: Generate or get root password
            passwd = self._get_or_generate_root_password()
            if not passwd:
                return False
                
            # Step 3: Create MySQL configuration file
            if not self._create_mysql_config():
                return False
                
            # Step 4: Create and start MySQL container
            config_data = self.config_manager.get()
            mysql_image = config_data.get("mysql", {}).get("version") or "mariadb:10.11"
            
            # Create MySQL compose
            template_path = os.path.join(env["TEMPLATES_DIR"], "docker-compose", "docker-compose.mysql.yml.template")
            output_path = os.path.join(env["INSTALL_DIR"], "docker-compose", "docker-compose.mysql.yml")
            
            # Create docker-compose directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            compose = Compose(
                name=mysql_container,
                template_path=template_path,
                output_path=output_path,
                env_map={
                    "PROJECT_NAME": project_name,
                    "MYSQL_CONTAINER_NAME": mysql_container,
                    "MYSQL_IMAGE": mysql_image,
                    "MYSQL_VOLUME_NAME": volume_name,
                    "DOCKER_NETWORK": docker_network,
                },
                sensitive_env={"mysql_root_passwd": passwd}
            )
            
            if not compose.ensure_ready():
                self.debug.error("Failed to create MySQL container")
                return False
                
            self.debug.success("MySQL bootstrap completed successfully")
            return True
        except Exception as e:
            self.debug.error(f"Failed to bootstrap MySQL: {e}")
            return False
        
    def mark_bootstrapped(self) -> None:
        """Mark MySQL as bootstrapped."""
        # MySQL bootstrap is marked by its configuration in the config file
        pass
        
    def _configure_mysql_version(self) -> bool:
        """
        Configure MySQL version if not already set.
        
        Returns:
            bool: True if successful, False otherwise
        """
        config_data = self.config_manager.get()
        
        # Skip if version is already configured
        if config_data.get("mysql", {}).get("version"):
            return True
            
        try:
            # Ask user to select MySQL version
            version_choices = [
                {"name": "MariaDB Latest", "value": "mariadb:latest"},
                {"name": "MariaDB 10.5", "value": "mariadb:10.5"},
                {"name": "MariaDB 10.6", "value": "mariadb:10.6"},
                {"name": "MariaDB 10.11", "value": "mariadb:10.11"},
            ]
            
            selected = questionary.select(
                "Select MariaDB version:",
                choices=version_choices
            ).ask()
            
            # Save selection to config
            mysql_data = config_data.get("mysql", {})
            mysql_data["version"] = selected
            self.config_manager.update_key("mysql", mysql_data)
            self.config_manager.save()
            
            self.debug.success(f"MariaDB version set to: {selected}")
            return True
        except Exception as e:
            self.debug.error(f"Failed to configure MySQL version: {e}")
            return False
            
    def _get_or_generate_root_password(self) -> Optional[str]:
        """
        Get existing or generate new MySQL root password.
        
        Returns:
            Optional[str]: Password or None if error
        """
        config_data = self.config_manager.get()
        
        try:
            # Use existing password if already set
            if config_data.get("mysql", {}).get("root_passwd"):
                return decrypt(config_data["mysql"]["root_passwd"])
                
            # Generate new password
            passwd = strong_password()
            mysql_data = config_data.get("mysql", {})
            mysql_data["root_passwd"] = encrypt(passwd)
            self.config_manager.update_key("mysql", mysql_data)
            self.config_manager.save()
            
            self.debug.debug("MySQL root password generated and saved")
            return passwd
        except Exception as e:
            self.debug.error(f"Failed to manage MySQL password: {e}")
            return None
            
    def _create_mysql_config(self) -> bool:
        """
        Create MySQL configuration file optimized for system resources.
        
        Returns:
            bool: True if successful, False otherwise
        """
        config_path = os.path.join(env["CONFIG_DIR"], "mysql.conf")
        
        # Skip if config file already exists
        if os.path.exists(config_path):
            self.debug.debug(f"MySQL config file already exists: {config_path}")
            return True
            
        try:
            self.debug.info(f"Creating MySQL configuration at: {config_path}")
            
            # Calculate optimal settings based on system resources
            total_ram = get_total_ram_mb()
            total_cpu = get_total_cpu_cores()
            
            max_connections = max(total_ram // 4, 100)
            query_cache_size = 32
            innodb_buffer_pool_size = max(total_ram // 2, 256)
            innodb_log_file_size = max(innodb_buffer_pool_size // 6, 64)
            table_open_cache = max(total_ram * 8, 400)
            thread_cache_size = max(total_cpu * 8, 16)
            
            # Create MySQL config file
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w") as f:
                f.write(f"""[mysqld]
max_connections = {max_connections}
query_cache_size = {query_cache_size}M
innodb_buffer_pool_size = {innodb_buffer_pool_size}M
innodb_log_file_size = {innodb_log_file_size}M
table_open_cache = {table_open_cache}
thread_cache_size = {thread_cache_size}
""")
            
            self.debug.success("MySQL configuration file created successfully")
            return True
        except Exception as e:
            self.debug.error(f"Failed to create MySQL config file: {e}")
            return False
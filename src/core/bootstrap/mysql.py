"""
MySQL bootstrap module.

This module handles MySQL container initialization, configuration,
and password management.
"""

import os
import questionary
from typing import Optional

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.common.utils.system_info import get_total_ram_mb, get_total_cpu_cores
from src.common.utils.crypto import encrypt, decrypt
from src.common.utils.password import strong_password
from src.core.bootstrap.base import BaseBootstrap
from src.common.config.manager import ConfigManager
from src.core.containers.compose import Compose
from src.common.containers.container import Container
from src.core.models.core_config import ContainerConfig


class MySQLBootstrap(BaseBootstrap):
    """Handles MySQL initialization and configuration."""

    debug = Debug("MySQLBootstrap")

    def __init__(self) -> None:
        """Initialize MySQL bootstrap."""
        super().__init__("MySQLBootstrap")
        self.config_manager = ConfigManager()

    @log_call
    def bootstrap(self) -> bool:
        """
        Override the base bootstrap method to ensure the config file exists
        even when bootstrap is skipped.

        Returns:
            bool: True if successful, False otherwise
        """
        # Skip if already bootstrapped, but still ensure config file exists
        if self.is_bootstrapped():
            self.debug.info("Already bootstrapped, skipping")

            # Even if bootstrapped, ensure the config file exists
            config_path = env["MYSQL_CONFIG_FILE"]
            if not os.path.exists(config_path):
                self.debug.warn("MySQL config file is missing but MySQL is considered bootstrapped")
                self.debug.info("Attempting to recreate the MySQL config file")
                self.ensure_mysql_config_file()

            return True

        # Continue with normal bootstrap process
        return super().bootstrap()

    def is_bootstrapped(self) -> bool:
        """
        Check if MySQL is already bootstrapped.

        Returns:
            bool: True if MySQL is already bootstrapped, False otherwise
        """
        # Check if MySQL configuration exists
        config_data = self.config_manager.get()

        # If no "mysql" key exists in config, bootstrap is needed
        if "mysql" not in config_data:
            self.debug.debug("❌ Bootstrap condition failed: MySQL key not found in config")
            return False

        if not config_data.get("mysql", {}).get("version"):
            self.debug.debug("❌ Bootstrap condition failed: MySQL version not configured in config")
            return False

        if not config_data.get("mysql", {}).get("root_passwd"):
            self.debug.debug("❌ Bootstrap condition failed: MySQL root password not configured in config")
            return False

        # Check if MySQL config file exists
        config_path = env["MYSQL_CONFIG_FILE"]
        if not os.path.exists(config_path):
            self.debug.debug(f"❌ Bootstrap condition failed: MySQL config file not found at {config_path}")
            return False

        # Check if MySQL compose file exists
        compose_path = os.path.join(env["INSTALL_DIR"], "docker-compose", "docker-compose.mysql.yml")
        if not os.path.exists(compose_path):
            self.debug.debug(f"❌ Bootstrap condition failed: MySQL docker-compose file not found at {compose_path}")
            return False

        # All bootstrap conditions satisfied
        self.debug.debug("✅ All MySQL bootstrap conditions satisfied:")
        self.debug.debug(f"  - MySQL version: {config_data.get('mysql', {}).get('version')}")
        self.debug.debug("  - MySQL root password: Configured (encrypted in config)")
        self.debug.debug(f"  - MySQL config file: {config_path}")
        self.debug.debug(f"  - MySQL compose file: {compose_path}")
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
            # Verify required environment variables are available
            required_vars = ["MYSQL_CONTAINER_NAME", "MYSQL_VOLUME_NAME", "DOCKER_NETWORK", 
                             "PROJECT_NAME", "MYSQL_CONFIG_FILE"]
            for var in required_vars:
                if var not in env:
                    self.debug.error(f"Required environment variable {var} not found")
                    return False
                self.debug.debug(f"Using {var}={env[var]}")

            # Get configuration details
            mysql_container = env["MYSQL_CONTAINER_NAME"]
            volume_name = env["MYSQL_VOLUME_NAME"]
            docker_network = env["DOCKER_NETWORK"]
            project_name = env["PROJECT_NAME"]
            config_path = env["MYSQL_CONFIG_FILE"]

            # Log important paths
            self.debug.debug(f"MySQL container name: {mysql_container}")
            self.debug.debug(f"MySQL config file path: {config_path}")
            
            # Ensure Docker network exists before continuing
            self._ensure_docker_network()

            # Step 1: Configure MySQL version
            if not self._configure_mysql_version():
                return False

            # Step 2: Generate or get root password
            passwd = self._get_or_generate_root_password()
            if not passwd:
                return False

            # Step 3: Create MySQL configuration file (using the ensure function)
            # Ensure config directory and file exist before creating the compose file
            if not self.ensure_mysql_config_file():
                return False

            # Step 4: Create and start MySQL container
            config_data = self.config_manager.get()
            mysql_image = config_data.get("mysql", {}).get("version") or "mariadb:10.11"

            # Create MySQL compose
            template_path = os.path.join(env["TEMPLATES_DIR"], "docker-compose", "docker-compose.mysql.yml.template")
            output_path = os.path.join(env["INSTALL_DIR"], "docker-compose", "docker-compose.mysql.yml")

            # Create docker-compose directory if it doesn't exist
            compose_dir = os.path.dirname(output_path)
            if not os.path.exists(compose_dir):
                self.debug.info(f"Creating docker-compose directory: {compose_dir}")
                os.makedirs(compose_dir, exist_ok=True)

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
            # --- Update container info in core config ---
            try:
                config_manager = ConfigManager()
                full_config = config_manager.get()
                core = full_config.get("core", {})
                containers = core.get("containers", [])

                container_obj = Container(env["MYSQL_CONTAINER_NAME"]).get()
                short_id = container_obj.config.hostname if container_obj and hasattr(container_obj, 'config') else ""

                # Remove old entry if MySQL already exists
                containers = [c for c in containers if c.get("name") != env["MYSQL_CONTAINER_NAME"]]

                containers.append(ContainerConfig(
                    name=env["MYSQL_CONTAINER_NAME"],
                    id=short_id,
                    compose_file=os.path.join(env["INSTALL_DIR"], "docker-compose", "docker-compose.mysql.yml")
                ).__dict__)

                core["containers"] = containers
                config_manager.update_key("core", core)
                config_manager.save()
            except Exception as e:
                self.debug.error(f"Failed to update MySQL container info in core config: {e}")
            # --- END container update ---
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
            # Use default values if interaction isn't possible
            import sys
            if not sys.stdin.isatty():
                self.debug.warn("Cannot interact with stdin, using MariaDB latest as default")
                selected = "mariadb:latest"
            else:
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
            if not mysql_data:
                mysql_data = {}

            mysql_data["version"] = selected
            self.config_manager.update_key("mysql", mysql_data)
            self.config_manager.save()

            self.debug.success(f"MariaDB version set to: {selected}")
            return True
        except Exception as e:
            self.debug.error(f"Failed to configure MySQL version: {e}")
            # If error occurs, try using a default value
            try:
                self.debug.info("Trying to use MariaDB latest after error")
                mysql_data = config_data.get("mysql", {})
                if not mysql_data:
                    mysql_data = {}

                mysql_data["version"] = "mariadb:latest"
                self.config_manager.update_key("mysql", mysql_data)
                self.config_manager.save()
                self.debug.success("Successfully set default MySQL version")
                return True
            except Exception as e2:
                self.debug.error(f"Also failed to set default MySQL version: {e2}")
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

    def ensure_mysql_config_file(self) -> bool:
        """
        Check if MySQL configuration file exists and create it if it doesn't.
        This can be called at any time, even after bootstrap.

        Returns:
            bool: True if config file exists or was created, False if error
        """
        config_path = env["MYSQL_CONFIG_FILE"]

        # If config file exists, return success
        if os.path.exists(config_path):
            self.debug.debug(f"MySQL config file exists: {config_path}")
            return True

        # Config file is missing, attempt to create it
        try:
            self.debug.info(f"MySQL config file is missing, creating at: {config_path}")

            # Calculate optimal settings based on system resources
            total_ram = get_total_ram_mb()
            total_cpu = get_total_cpu_cores()

            max_connections = max(total_ram // 4, 100)
            query_cache_size = 32
            innodb_buffer_pool_size = max(total_ram // 2, 256)
            innodb_log_file_size = max(innodb_buffer_pool_size // 6, 64)
            table_open_cache = max(total_ram * 8, 400)
            thread_cache_size = max(total_cpu * 8, 16)

            # Ensure directory exists
            mysql_conf_dir = os.path.dirname(config_path)
            if not os.path.exists(mysql_conf_dir):
                self.debug.info(f"Creating MySQL config directory: {mysql_conf_dir}")
                os.makedirs(mysql_conf_dir, exist_ok=True)

            # Create MySQL config file
            with open(config_path, "w") as f:
                f.write(f"""[mysqld]
max_connections = {max_connections}
query_cache_size = {query_cache_size}M
innodb_buffer_pool_size = {innodb_buffer_pool_size}M
innodb_log_file_size = {innodb_log_file_size}M
table_open_cache = {table_open_cache}
thread_cache_size = {thread_cache_size}
""")

            self.debug.success("✅ MySQL configuration file created successfully")

            # Check if MySQL container is running and restart it to apply changes
            container = Container(env["MYSQL_CONTAINER_NAME"])
            if container.running():
                self.debug.info("MySQL container is running, restarting to apply new configuration")
                container.restart()

            return True
        except Exception as e:
            self.debug.error(f"❌ Failed to create MySQL config file: {e}")
            return False

    def _create_mysql_config(self) -> bool:
        """
        Create MySQL configuration file optimized for system resources.
        Used during bootstrap only.

        Returns:
            bool: True if successful, False otherwise
        """
        # Delegate to the ensure_mysql_config_file function
        return self.ensure_mysql_config_file()
        
    def _ensure_docker_network(self) -> bool:
        """
        Ensure the Docker network required by MySQL exists.
        
        This method checks if the network defined in DOCKER_NETWORK exists,
        and creates it if it doesn't.
        
        Returns:
            bool: True if the network exists or was created, False if error
        """
        network = env["DOCKER_NETWORK"]
        try:
            import subprocess
            
            # Check if network exists
            self.debug.info(f"Checking if Docker network {network} exists...")
            result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{.Name}}"],
                capture_output=True, text=True
            )
            
            # If command failed, log and return False
            if result.returncode != 0:
                self.debug.error(f"Failed to check Docker networks: {result.stderr}")
                return False
                
            networks = result.stdout.strip().splitlines()
            
            # If network doesn't exist, create it
            if network not in networks:
                self.debug.warn(f"Docker network {network} not found, creating it...")
                create_result = subprocess.run(
                    ["docker", "network", "create", network],
                    capture_output=True, text=True
                )
                
                if create_result.returncode != 0:
                    self.debug.error(f"Failed to create Docker network: {create_result.stderr}")
                    return False
                    
                self.debug.success(f"Created Docker network: {network}")
            else:
                self.debug.info(f"Docker network {network} already exists")
                
            return True
        except Exception as e:
            self.debug.error(f"Error checking/creating Docker network: {e}")
            return False
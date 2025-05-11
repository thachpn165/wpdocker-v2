"""
Rclone bootstrap module.

This module handles Rclone remote storage initialization, configuration,
and container setup.
"""

import os

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.core.bootstrap.base import BaseBootstrap
from src.core.containers.compose import Compose


@log_call
class RcloneBootstrap(BaseBootstrap):
    """Handles Rclone initialization and configuration."""

    debug = Debug("RcloneBootstrap")

    def __init__(self) -> None:
        """Initialize Rclone bootstrap."""
        super().__init__("RcloneBootstrap")

        # Configuration paths
        self.config_dir = env.get("CONFIG_DIR", "/opt/wp-docker/src/config")
        self.rclone_config_dir = os.path.join(self.config_dir, "rclone")
        self.rclone_config_file = os.path.join(self.rclone_config_dir, "rclone.conf")

        # Compose file paths
        install_dir = env.get("INSTALL_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
        docker_compose_dir = os.path.join(install_dir, "docker-compose")
        templates_dir = env.get("TEMPLATES_DIR", os.path.join(install_dir, "src/templates"))

        self.compose_file = os.path.join(docker_compose_dir, "docker-compose.rclone.yml")
        self.template_file = os.path.join(templates_dir, "docker-compose", "docker-compose.rclone.yml.template")

        # Environment variables
        self.project_name = env.get("PROJECT_NAME", "wpdocker")
        self.rclone_container_name = env.get("RCLONE_CONTAINER_NAME", "wpdocker_rclone")
        self.rclone_image = env.get("RCLONE_IMAGE", "rclone/rclone:latest")
        self.docker_network = env.get("DOCKER_NETWORK", "wpdocker_net")
        self.data_dir = env.get("DATA_DIR", os.path.join(install_dir, "data"))
        self.backup_dir = env.get("BACKUP_DIR", os.path.join(self.data_dir, "backups"))
        self.timezone = env.get("TIMEZONE", "Asia/Ho_Chi_Minh")

    def is_bootstrapped(self) -> bool:
        """
        Check if Rclone is already bootstrapped.

        Returns:
            bool: True if Rclone is already bootstrapped, False otherwise
        """
        # Check if Rclone configuration directory and file exist
        if not os.path.exists(self.rclone_config_dir):
            return False

        if not os.path.exists(self.rclone_config_file):
            return False

        # Check if Rclone compose file exists
        if not os.path.exists(self.compose_file):
            return False

        return True

    def check_prerequisites(self) -> bool:
        """
        Check if prerequisites for Rclone bootstrap are met.

        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        required_env_vars = [
            "PROJECT_NAME",
            "DOCKER_NETWORK",
            "INSTALL_DIR",
            "CONFIG_DIR",
            "DATA_DIR",
            "TEMPLATES_DIR",
            "RCLONE_CONTAINER_NAME"
        ]

        for var in required_env_vars:
            if var not in env:
                self.debug.warn(f"Environment variable {var} not set, using default value")

        # Check if template file exists
        if not os.path.exists(self.template_file):
            self.debug.error(f"Rclone compose template not found: {self.template_file}")
            return False

        return True

    def execute_bootstrap(self) -> bool:
        """
        Execute the Rclone bootstrap process.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.debug.info("Initializing Rclone...")

            # Step 1: Ensure directories exist
            if not self._ensure_directories():
                return False

            # Step 2: Ensure configuration file exists
            if not self._ensure_config_file():
                return False

            # Step 3: Create and start Rclone container
            if not self._create_rclone_container():
                return False

            self.debug.success("Rclone bootstrap completed successfully")
            # --- Cập nhật thông tin container vào core config ---
            try:
                from src.core.config.manager import ConfigManager
                from src.core.models.core_config import ContainerConfig
                from src.common.containers.container import Container

                config_manager = ConfigManager()
                full_config = config_manager.get()
                core = full_config.get("core", {})
                containers = core.get("containers", [])

                container_obj = Container(self.rclone_container_name).get()
                short_id = container_obj.config.hostname if container_obj and hasattr(container_obj, 'config') else ""

                # Xóa entry cũ nếu đã có rclone
                containers = [c for c in containers if c.get("name") != self.rclone_container_name]

                containers.append(ContainerConfig(
                    name=self.rclone_container_name,
                    id=short_id,
                    compose_file=self.compose_file
                ).__dict__)

                core["containers"] = containers
                config_manager.update_key("core", core)
                config_manager.save()
            except Exception as e:
                self.debug.error(f"Failed to update rclone container info in core config: {e}")
            # --- END cập nhật container ---
            return True
        except Exception as e:
            self.debug.error(f"Failed to bootstrap Rclone: {e}")
            return False

    def mark_bootstrapped(self) -> None:
        """Mark Rclone as bootstrapped."""
        # Rclone bootstrap is marked by the presence of its configuration files
        pass

    def _ensure_directories(self) -> bool:
        """
        Ensure all required directories exist.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure Rclone configuration directory exists
            os.makedirs(self.rclone_config_dir, exist_ok=True)

            # Ensure backup directory exists
            os.makedirs(self.backup_dir, exist_ok=True)

            # Ensure docker-compose directory exists
            os.makedirs(os.path.dirname(self.compose_file), exist_ok=True)

            self.debug.debug("Required directories created")
            return True
        except Exception as e:
            self.debug.error(f"Failed to create required directories: {e}")
            return False

    def _ensure_config_file(self) -> bool:
        """
        Ensure the Rclone configuration file exists.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.rclone_config_file):
                # Create an empty configuration file
                open(self.rclone_config_file, "w").close()  # Empty file, will be populated by the Rclone manager

                self.debug.info(f"Created empty Rclone configuration file: {self.rclone_config_file}")
                self.debug.debug(f"Rclone configuration file already exists: {self.rclone_config_file}")

            return True
        except Exception as e:
            self.debug.error(f"Failed to create Rclone configuration file: {e}")
            return False

    def _create_rclone_container(self) -> bool:
        """
        Create and start Rclone container.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create Compose object
            compose = Compose(
                name=self.rclone_container_name,
                template_path=self.template_file,
                output_path=self.compose_file,
                env_map={
                    "PROJECT_NAME": self.project_name,
                    "RCLONE_CONTAINER_NAME": self.rclone_container_name,
                    "RCLONE_IMAGE": self.rclone_image,
                    "CONFIG_DIR": self.config_dir,
                    "DATA_DIR": self.data_dir,
                    "BACKUP_DIR": self.backup_dir,
                    "DOCKER_NETWORK": self.docker_network,
                    "TIMEZONE": self.timezone
                }
            )

            if not compose.ensure_ready():
                self.debug.error("Failed to create Rclone container")
                return False

            self.debug.success(f"Rclone container created: {self.rclone_container_name}")
            return True
        except Exception as e:
            self.debug.error(f"Failed to create Rclone container: {e}")
            return False

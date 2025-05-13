"""
Redis bootstrap module.

This module handles Redis container initialization and configuration.
"""

import os

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.core.bootstrap.base import BaseBootstrap
from src.core.containers.compose import Compose


@log_call
class RedisBootstrap(BaseBootstrap):
    """Handles Redis initialization and configuration."""
    debug = Debug("RedisBootstrap")

    def __init__(self) -> None:
        """Initialize Redis bootstrap."""
        super().__init__("RedisBootstrap")
        self.redis_container_name = env.get("REDIS_CONTAINER_NAME", "wpdocker_redis")
        install_dir = env.get("INSTALL_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
        docker_compose_dir = os.path.join(install_dir, "docker-compose")
        self.compose_file = os.path.join(docker_compose_dir, "docker-compose.redis.yml")

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
            # --- Cập nhật thông tin container vào core config ---
            try:
                from src.common.config.manager import ConfigManager
                from src.core.models.core_config import ContainerConfig
                from src.common.containers.container import Container

                config_manager = ConfigManager()
                full_config = config_manager.get()
                core = full_config.get("core", {})
                containers = core.get("containers", [])

                container_obj = Container(self.redis_container_name).get()
                short_id = container_obj.config.hostname if container_obj and hasattr(container_obj, 'config') else ""

                # Xóa entry cũ nếu đã có redis
                containers = [c for c in containers if c.get("name") != self.redis_container_name]

                containers.append(ContainerConfig(
                    name=self.redis_container_name,
                    id=short_id,
                    compose_file=self.compose_file
                ).__dict__)

                core["containers"] = containers
                config_manager.update_key("core", core)
                config_manager.save()
            except Exception as e:
                self.debug.error(f"Failed to update redis container info in core config: {e}")
            # --- END cập nhật container ---
            return True
        except Exception as e:
            self.debug.error(f"Failed to bootstrap Redis: {e}")
            return False

    def mark_bootstrapped(self) -> None:
        """Mark Redis as bootstrapped."""
        # Redis bootstrap is marked by the presence of its compose file
        pass

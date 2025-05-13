"""
NGINX bootstrap module.

This module handles NGINX webserver initialization, configuration,
and container setup.
"""

import os

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.core.bootstrap.base import BaseBootstrap
from src.core.containers.compose import Compose
from src.core.containers.container import Container
from src.features.website.utils import website_list
from questionary import confirm


@log_call
class NginxBootstrap(BaseBootstrap):
    debug = Debug("NginxBootstrap")
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
            "TEMPLATES_DIR",
            "NGINX_CONFIG_DIR"
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

            # Step 4: Check and (optionally) recreate missing website configs
            if not self._check_and_recreate_site_configs():
                return False

            self.debug.success("NGINX bootstrap completed successfully")
            # --- Cập nhật thông tin container vào core config ---
            try:
                from src.common.config.manager import ConfigManager
                from src.core.models.core_config import ContainerConfig
                from src.common.containers.container import Container

                config_manager = ConfigManager()
                full_config = config_manager.get()
                core = full_config.get("core", {})
                containers = core.get("containers", [])

                # Đảm bảo có self.nginx_container_name và self.compose_file
                nginx_container_name = getattr(self, 'nginx_container_name', env.get("NGINX_CONTAINER_NAME", "wpdocker_nginx"))
                compose_file = getattr(self, 'compose_file', os.path.join(env["INSTALL_DIR"], "docker-compose", "docker-compose.nginx.yml"))

                container_obj = Container(nginx_container_name).get()
                short_id = container_obj.config.hostname if container_obj and hasattr(container_obj, 'config') else ""

                # Xóa entry cũ nếu đã có nginx
                containers = [c for c in containers if c.get("name") != nginx_container_name]

                containers.append(ContainerConfig(
                    name=nginx_container_name,
                    id=short_id,
                    compose_file=compose_file
                ).__dict__)

                core["containers"] = containers
                config_manager.update_key("core", core)
                config_manager.save()
            except Exception as e:
                self.debug.error(f"Failed to update nginx container info in core config: {e}")
            # --- END cập nhật container ---
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
            nginx_conf_dir = env["NGINX_CONFIG_DIR"]
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

            # Ensure FastCGI cache volume exists
            self._ensure_fastcgi_cache_volume_exists()

            # Define FastCGI cache volume name
            fastcgi_cache_volume = "wpdocker_fastcgi_cache_data"

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
                    "NGINX_CONTAINER_CONF_PATH": env["NGINX_CONTAINER_CONF_PATH"],
                    "NGINX_CONFIG_DIR": env["NGINX_CONFIG_DIR"],
                    "CONFIG_DIR": env["CONFIG_DIR"],
                    "SITES_DIR": env["SITES_DIR"],
                    "FASTCGI_CACHE_VOLUME": fastcgi_cache_volume,
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

    def _ensure_fastcgi_cache_volume_exists(self) -> bool:
        """
        Ensure the FastCGI cache volume exists.

        Returns:
            bool: True if successful, False otherwise
        """
        import subprocess

        try:
            # Check if volume exists
            result = subprocess.run(
                ["docker", "volume", "ls", "--format", "{{.Name}}"],
                capture_output=True, text=True, check=True
            )
            volumes = result.stdout.strip().splitlines()
            volume_name = "wpdocker_fastcgi_cache_data"

            # Create volume if it doesn't exist
            if volume_name not in volumes:
                self.debug.info(f"FastCGI cache volume not found, creating it: {volume_name}")
                subprocess.run(
                    ["docker", "volume", "create", volume_name],
                    check=True
                )
                self.debug.success(f"Created Docker volume for FastCGI cache: {volume_name}")
            else:
                self.debug.debug(f"FastCGI cache volume already exists: {volume_name}")

            return True
        except Exception as e:
            self.debug.error(f"Failed to ensure FastCGI cache volume exists: {e}")
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

    def _check_and_recreate_site_configs(self) -> bool:
        """
        Kiểm tra và tái tạo file cấu hình NGINX cho từng website nếu thiếu.
        """
        try:
            sites = website_list()
            nginx_conf_dir = os.path.join(env["CONFIG_DIR"], "nginx", "conf.d")
            template_path = os.path.join(env["TEMPLATES_DIR"], "nginx", "nginx-domain.conf.template")
            for domain in sites:
                conf_file = os.path.join(nginx_conf_dir, f"{domain}.conf")
                if not os.path.exists(conf_file):
                    self.debug.warn(f"⚠️ NGINX config missing for website {domain}: {conf_file}")
                    answer = confirm(f"File cấu hình NGINX cho website {domain} bị thiếu. Bạn có muốn tái tạo file này không? ({conf_file})").ask()
                    if answer:
                        with open(template_path, "r") as f:
                            content = f.read()
                        # Thay thế biến trong template
                        content = content.replace("${DOMAIN}", domain)
                        # Có thể bổ sung các biến khác nếu cần
                        os.makedirs(nginx_conf_dir, exist_ok=True)
                        with open(conf_file, "w") as f:
                            f.write(content)
                        self.debug.success(f"Đã tái tạo file cấu hình NGINX cho website {domain}: {conf_file}")
                    else:
                        self.debug.error(f"Người dùng từ chối tái tạo file cấu hình cho {domain}. Website này sẽ không hoạt động!")
            return True
        except Exception as e:
            self.debug.error(f"Lỗi khi kiểm tra/tái tạo file cấu hình NGINX cho website: {e}")
            return False

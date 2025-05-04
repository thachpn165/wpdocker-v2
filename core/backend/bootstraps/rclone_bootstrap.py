#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path

from core.backend.objects.compose import Compose
from core.backend.objects.config import Config
from core.backend.utils.env_utils import get_env_value
from core.backend.utils.validate import validate_directory


class RcloneBootstrap:
    """Bootstrap class for Rclone configuration and initialization."""

    def __init__(self, config=None):
        self.config = config or Config()
        self.force_update = False
        if config and hasattr(config, 'force_update'):
            self.force_update = config.force_update
        
        # Đảm bảo có các biến môi trường cần thiết, sử dụng giá trị mặc định nếu không có
        config_dir = get_env_value("CONFIG_DIR", "/opt/wp-docker/config")
        self.rclone_config_dir = os.path.join(config_dir, "rclone")
        self.rclone_config_file = os.path.join(self.rclone_config_dir, "rclone.conf")
        
        # Ensure config directory exists
        os.makedirs(self.rclone_config_dir, exist_ok=True)
        
        # Xác định các đường dẫn dựa trên cấu trúc project
        install_dir = get_env_value("INSTALL_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
        docker_compose_dir = get_env_value("DOCKER_COMPOSE_DIR", os.path.join(install_dir, "docker-compose"))
        core_templates_dir = get_env_value("CORE_TEMPLATES_DIR", os.path.join(install_dir, "core/templates"))
        
        # Docker compose management
        self.compose_file = os.path.join(docker_compose_dir, "docker-compose.rclone.yml")
        self.template_file = os.path.join(core_templates_dir, "docker-compose.rclone.yml.template")
        
        # Đảm bảo biến môi trường cho rclone
        project_name = get_env_value("PROJECT_NAME", "wpdocker")
        rclone_container_name = get_env_value("RCLONE_CONTAINER_NAME", "wpdocker_rclone")
        rclone_image = get_env_value("RCLONE_IMAGE", "rclone/rclone:latest")
        docker_network = get_env_value("DOCKER_NETWORK", "wpdocker_net")
        data_dir = get_env_value("DATA_DIR", os.path.join(install_dir, "data"))
        backup_dir = get_env_value("BACKUP_DIR", os.path.join(data_dir, "backups"))
        timezone = get_env_value("TIMEZONE", "Asia/Ho_Chi_Minh")
        
        # Create Compose object
        self.compose = Compose(
            name=rclone_container_name,
            template_path=self.template_file,
            output_path=self.compose_file,
            env_map={
                "PROJECT_NAME": project_name,
                "RCLONE_CONTAINER_NAME": rclone_container_name,
                "RCLONE_IMAGE": rclone_image,
                "CONFIG_DIR": config_dir,
                "DATA_DIR": data_dir,
                "BACKUP_DIR": backup_dir,
                "DOCKER_NETWORK": docker_network,
                "TIMEZONE": timezone
            }
        )

    def bootstrap(self):
        """Initialize Rclone configuration and docker-compose file."""
        # Ensure directories exist
        self._ensure_directories()
        
        # Ensure the rclone.conf file exists
        self._ensure_config_file()
        
        # Make sure Docker Compose file is ready and container is running
        self.compose.ensure_ready()
        
        return True

    def _ensure_directories(self):
        """Ensure all required directories exist."""
        validate_directory(self.rclone_config_dir)
        
        # Create backup directory if it doesn't exist
        backup_dir = self.compose.env_map.get("BACKUP_DIR")
        validate_directory(backup_dir)

    def _create_docker_compose(self):
        """Create or update the docker-compose file for Rclone."""
        if not os.path.exists(self.compose_file) or self.force_update:
            self.compose.generate_compose_file()
            return True
        return False

    def _ensure_config_file(self):
        """Ensure the rclone.conf file exists."""
        if not os.path.exists(self.rclone_config_file):
            # Create an empty config file if it doesn't exist
            with open(self.rclone_config_file, "w") as f:
                pass  # Empty file, will be populated by the Rclone manager
            return True
        return False

    def get_status(self):
        """Get the current status of Rclone configuration."""
        status = {
            "config_dir_exists": os.path.exists(self.rclone_config_dir),
            "config_file_exists": os.path.exists(self.rclone_config_file),
            "docker_compose_exists": os.path.exists(self.compose_file)
        }
        return status
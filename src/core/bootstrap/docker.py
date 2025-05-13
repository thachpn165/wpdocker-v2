"""
Docker bootstrap module.

This module handles Docker initialization, network and volume creation,
and user permissions.
"""

import subprocess
import platform
import os
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
        # Docker được coi là đã bootstrap chỉ khi đã được cài đặt
        # (nhưng chúng ta vẫn sẽ kiểm tra và khởi động nếu không chạy)
        try:
            subprocess.run(
                ["docker", "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # Docker đã được cài đặt, nhưng chúng ta vẫn sẽ kiểm tra trạng thái,
            # network và volume trong execute_bootstrap
            return True
        except Exception:
            self.debug.error("Docker chưa được cài đặt")
            return False

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
        if not self._is_docker_installed():
            self.debug.info("Docker chưa được cài đặt, đang cài đặt...")
            if not install_docker_if_missing():
                self.debug.error("Docker installation failed")
                return False
            self.debug.success("Docker đã được cài đặt thành công")
        else:
            self.debug.info("Docker đã được cài đặt")

        # Step 2: Verify Docker is running, nếu chưa thì thử khởi động
        if not self._is_docker_running():
            self.debug.warn("Docker không chạy, đang thử khởi động...")
            if self._start_docker_service():
                self.debug.success("Đã khởi động Docker")
            # Kiểm tra lại sau khi thử khởi động
            if not self._is_docker_running():
                self.debug.error("Docker vẫn không chạy sau khi thử khởi động")
                return False
        else:
            self.debug.info("Docker đang chạy")

        # Step 3: Create Docker network
        if not self._create_docker_network():
            self.debug.error("Không thể tạo Docker network")
            return False

        # Step 4: Create MySQL data volume
        if not self._create_mysql_volume():
            self.debug.error("Không thể tạo volume dữ liệu MySQL")
            return False

        # Step 5: Create FastCGI cache volume
        if not self._create_fastcgi_cache_volume():
            self.debug.error("Không thể tạo volume FastCGI cache")
            return False

        # Step 6: Add user to Docker group (Linux only)
        if platform.system() != "Darwin":
            if not self._add_user_to_docker_group():
                self.debug.warn("Không thể thêm người dùng vào nhóm Docker")
                # This is not a critical failure

        self.debug.success("Docker đã được thiết lập đầy đủ")
        return True

    def mark_bootstrapped(self) -> None:
        """Mark Docker as bootstrapped."""
        # Docker bootstrap doesn't need explicit marking
        pass

    def _is_docker_installed(self) -> bool:
        """
        Kiểm tra xem Docker đã được cài đặt hay chưa.

        Returns:
            bool: True nếu Docker đã được cài đặt, False nếu chưa
        """
        try:
            subprocess.run(
                ["docker", "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            return False

    def _is_docker_running(self) -> bool:
        """
        Kiểm tra xem Docker có đang chạy hay không.

        Returns:
            bool: True nếu Docker đang chạy, False nếu không chạy
        """
        try:
            subprocess.run(
                ["docker", "info"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            # Chỉ ghi log lỗi khi Docker đã được cài đặt nhưng không chạy
            if self._is_docker_installed():
                self.debug.error("Docker đã cài đặt nhưng không chạy")
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

    def _create_mysql_volume(self) -> bool:
        """
        Tạo volume lưu trữ dữ liệu MySQL nếu chưa tồn tại.

        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            result = subprocess.run(
                ["docker", "volume", "ls", "--format", "{{.Name}}"],
                capture_output=True, text=True
            )
            volumes = result.stdout.strip().splitlines()
            volume_name = env.get("MYSQL_VOLUME_NAME", "wpdocker_mysql_data")

            if volume_name not in volumes:
                subprocess.run(
                    ["docker", "volume", "create", volume_name],
                    check=True
                )
                self.debug.success(f"Đã tạo volume MySQL: {volume_name}")
            else:
                self.debug.debug(f"Volume MySQL đã tồn tại: {volume_name}")

            return True
        except Exception as e:
            self.debug.error(f"Không thể tạo volume MySQL: {e}")
            return False

    def _create_fastcgi_cache_volume(self) -> bool:
        """
        Tạo volume lưu trữ FastCGI cache nếu chưa tồn tại.

        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            result = subprocess.run(
                ["docker", "volume", "ls", "--format", "{{.Name}}"],
                capture_output=True, text=True
            )
            volumes = result.stdout.strip().splitlines()
            volume_name = env.get("FASTCGI_CACHE_VOLUME", "wpdocker_fastcgi_cache_data")

            if volume_name not in volumes:
                subprocess.run(
                    ["docker", "volume", "create", volume_name],
                    check=True
                )
                self.debug.success(f"Đã tạo volume FastCGI cache: {volume_name}")
            else:
                self.debug.debug(f"Volume FastCGI cache đã tồn tại: {volume_name}")

            return True
        except Exception as e:
            self.debug.error(f"Không thể tạo volume FastCGI cache: {e}")
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

    def _start_docker_service(self) -> bool:
        """
        Start Docker service cross-platform (Linux/macOS).
        Returns True nếu khởi động thành công hoặc đã chạy, False nếu lỗi.
        """
        import sys
        try:
            if sys.platform == "darwin":
                # macOS: mở Docker Desktop
                result = subprocess.run(["open", "--background", "-a", "Docker"])
                self.debug.info("Đã chạy lệnh mở Docker Desktop trên macOS.")
                return result.returncode == 0
            elif sys.platform.startswith("linux"):
                # Linux: thử systemctl trước, fallback sang service
                result = subprocess.run(["sudo", "systemctl", "start", "docker"])
                if result.returncode != 0:
                    result = subprocess.run(["sudo", "service", "docker", "start"])
                self.debug.info("Đã chạy lệnh khởi động Docker trên Linux.")
                return result.returncode == 0
            else:
                self.debug.warn("Không hỗ trợ tự động khởi động Docker trên hệ điều hành này.")
                return False
        except Exception as e:
            self.debug.error(f"Lỗi khi khởi động Docker: {e}")
            return False

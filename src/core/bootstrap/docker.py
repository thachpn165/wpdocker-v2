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
        # Check if Docker is installed
        try:
            subprocess.run(
                ["docker", "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            self.debug.error("Docker is not installed")
            return False
            
        # Check if Docker is running
        if not self._is_docker_running():
            self.debug.warn("Docker is installed but not running")
            return False
            
        # Check if Docker network and volumes exist
        # IMPORTANT: Only mark as bootstrapped when all required networks and volumes exist
        
        # Check network
        if not self._check_docker_network_exists():
            self.debug.warn(f"Docker network {env['DOCKER_NETWORK']} does not exist")
            return False
            
        # Check MySQL volume
        volume_name = env.get("MYSQL_VOLUME_NAME", "wpdocker_mysql_data")
        if not self._check_volume_exists(volume_name):
            self.debug.warn(f"Docker volume {volume_name} does not exist")
            return False
            
        # Check FastCGI volume
        fcgi_volume = env.get("FASTCGI_CACHE_VOLUME", "wpdocker_fastcgi_cache_data")
        if not self._check_volume_exists(fcgi_volume):
            self.debug.warn(f"Docker volume {fcgi_volume} does not exist")
            return False
            
        # All conditions are met
        self.debug.info("Docker is fully bootstrapped with required networks and volumes")
        return True

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
            self.debug.info("Docker not installed, installing...")
            if not install_docker_if_missing():
                self.debug.error("Docker installation failed")
                return False
            self.debug.success("Docker installed successfully")
        else:
            self.debug.info("Docker is already installed")

        # Step 2: Verify Docker is running, try to start if not
        if not self._is_docker_running():
            self.debug.warn("Docker not running, attempting to start...")
            if self._start_docker_service():
                self.debug.success("Docker started")
            # Verify after trying to start
            if not self._is_docker_running():
                self.debug.error("Docker still not running after start attempt")
                return False
        else:
            self.debug.info("Docker is running")

        # Step 3: Create Docker network
        if not self._create_docker_network():
            self.debug.error("Failed to create Docker network")
            return False
            
        # Verify network exists after creation
        if not self._check_docker_network_exists():
            self.debug.error(f"Failed to verify network {env['DOCKER_NETWORK']} after creation")
            return False

        # Step 4: Create MySQL data volume
        if not self._create_mysql_volume():
            self.debug.error("Failed to create MySQL data volume")
            return False
            
        # Verify MySQL volume exists
        volume_name = env.get("MYSQL_VOLUME_NAME", "wpdocker_mysql_data")
        if not self._check_volume_exists(volume_name):
            self.debug.error(f"Failed to verify volume {volume_name} after creation")
            return False

        # Step 5: Create FastCGI cache volume
        if not self._create_fastcgi_cache_volume():
            self.debug.error("Failed to create FastCGI cache volume")
            return False
            
        # Verify FastCGI volume exists
        fcgi_volume = env.get("FASTCGI_CACHE_VOLUME", "wpdocker_fastcgi_cache_data")
        if not self._check_volume_exists(fcgi_volume):
            self.debug.error(f"Failed to verify volume {fcgi_volume} after creation")
            return False

        # Step 6: Add user to Docker group (Linux only)
        if platform.system() != "Darwin":
            if not self._add_user_to_docker_group():
                self.debug.warn("Could not add user to Docker group")
                # This is not a critical failure

        self.debug.success("Docker setup complete")
        return True

    def mark_bootstrapped(self) -> None:
        """Mark Docker as bootstrapped."""
        # Docker bootstrap doesn't need explicit marking
        pass

    def _is_docker_installed(self) -> bool:
        """
        Check if Docker is installed.

        Returns:
            bool: True if Docker is installed, False otherwise
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
            return True
        except Exception:
            # Only log error when Docker is installed but not running
            if self._is_docker_installed():
                self.debug.error("Docker is installed but not running")
            return False

    def _check_docker_network_exists(self) -> bool:
        """
        Check if the Docker network exists.
        
        Returns:
            bool: True if the network exists, False otherwise
        """
        if "DOCKER_NETWORK" not in env:
            self.debug.error("DOCKER_NETWORK environment variable is not set")
            return False
            
        network = env["DOCKER_NETWORK"]
        try:
            result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{.Name}}"],
                capture_output=True, text=True, check=True
            )
            
            if result.returncode != 0:
                self.debug.error(f"Failed to list Docker networks: {result.stderr}")
                return False
                
            networks = result.stdout.strip().splitlines()
            exists = network in networks
            
            if exists:
                self.debug.debug(f"Docker network {network} exists")
            else:
                self.debug.debug(f"Docker network {network} does not exist")
                
            return exists
        except Exception as e:
            self.debug.error(f"Error checking Docker network: {e}")
            return False
    
    def _check_volume_exists(self, volume_name: str) -> bool:
        """
        Check if a Docker volume exists.
        
        Args:
            volume_name: Name of the volume to check
            
        Returns:
            bool: True if the volume exists, False otherwise
        """
        try:
            result = subprocess.run(
                ["docker", "volume", "ls", "--format", "{{.Name}}"],
                capture_output=True, text=True, check=True
            )
            
            if result.returncode != 0:
                self.debug.error(f"Failed to list Docker volumes: {result.stderr}")
                return False
                
            volumes = result.stdout.strip().splitlines()
            exists = volume_name in volumes
            
            if exists:
                self.debug.debug(f"Docker volume {volume_name} exists")
            else:
                self.debug.debug(f"Docker volume {volume_name} does not exist")
                
            return exists
        except Exception as e:
            self.debug.error(f"Error checking Docker volume: {e}")
            return False
    
    def _create_docker_network(self) -> bool:
        """
        Create Docker network if it doesn't exist.

        Returns:
            bool: True if successful, False otherwise
        """
        if "DOCKER_NETWORK" not in env:
            self.debug.error("DOCKER_NETWORK environment variable is not set")
            return False
            
        network = env["DOCKER_NETWORK"]
        
        # Check if network already exists
        if self._check_docker_network_exists():
            self.debug.info(f"Docker network already exists: {network}")
            return True
            
        # Network doesn't exist, create it
        try:
            self.debug.info(f"Creating Docker network: {network}")
            create_result = subprocess.run(
                ["docker", "network", "create", network],
                capture_output=True, text=True
            )
            
            if create_result.returncode != 0:
                self.debug.error(f"Failed to create Docker network: {create_result.stderr}")
                return False
                
            self.debug.success(f"Created Docker network: {network}")
            
            # Verify network was created successfully
            verify_result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{.Name}}"],
                capture_output=True, text=True
            )
            
            if verify_result.returncode != 0:
                self.debug.error(f"Failed to verify network creation: {verify_result.stderr}")
                return False
                
            networks = verify_result.stdout.strip().splitlines()
            if network not in networks:
                self.debug.error(f"Docker network {network} was not created successfully")
                return False
                
            self.debug.info(f"Verified Docker network {network} was created successfully")
            return True
        except Exception as e:
            self.debug.error(f"Failed to create Docker network: {e}")
            return False

    def _create_mysql_volume(self) -> bool:
        """
        Create MySQL data volume if it doesn't exist.

        Returns:
            bool: True if successful, False otherwise
        """
        volume_name = env.get("MYSQL_VOLUME_NAME", "wpdocker_mysql_data")
        
        # Check if volume already exists
        if self._check_volume_exists(volume_name):
            self.debug.info(f"MySQL volume already exists: {volume_name}")
            return True
            
        # Volume doesn't exist, create it
        try:
            self.debug.info(f"Creating MySQL volume: {volume_name}")
            create_result = subprocess.run(
                ["docker", "volume", "create", volume_name],
                capture_output=True, text=True
            )
            
            if create_result.returncode != 0:
                self.debug.error(f"Error creating MySQL volume: {create_result.stderr}")
                return False
                
            self.debug.success(f"Created MySQL volume: {volume_name}")
            
            # Verify volume was created successfully
            verify_result = subprocess.run(
                ["docker", "volume", "ls", "--format", "{{.Name}}"],
                capture_output=True, text=True
            )
            
            if verify_result.returncode != 0:
                self.debug.error(f"Failed to verify MySQL volume creation: {verify_result.stderr}")
                return False
                
            volumes = verify_result.stdout.strip().splitlines()
            if volume_name not in volumes:
                self.debug.error(f"MySQL volume {volume_name} was not created successfully")
                return False
                
            self.debug.info(f"Verified MySQL volume {volume_name} was created successfully")
            return True
        except Exception as e:
            self.debug.error(f"Failed to create MySQL volume: {e}")
            return False

    def _create_fastcgi_cache_volume(self) -> bool:
        """
        Create FastCGI cache volume if it doesn't exist.

        Returns:
            bool: True if successful, False otherwise
        """
        volume_name = env.get("FASTCGI_CACHE_VOLUME", "wpdocker_fastcgi_cache_data")
        
        # Check if volume already exists
        if self._check_volume_exists(volume_name):
            self.debug.info(f"FastCGI cache volume already exists: {volume_name}")
            return True
            
        # Volume doesn't exist, create it
        try:
            self.debug.info(f"Creating FastCGI cache volume: {volume_name}")
            create_result = subprocess.run(
                ["docker", "volume", "create", volume_name],
                capture_output=True, text=True
            )
            
            if create_result.returncode != 0:
                self.debug.error(f"Error creating FastCGI cache volume: {create_result.stderr}")
                return False
                
            self.debug.success(f"Created FastCGI cache volume: {volume_name}")
            
            # Verify volume was created successfully
            verify_result = subprocess.run(
                ["docker", "volume", "ls", "--format", "{{.Name}}"],
                capture_output=True, text=True
            )
            
            if verify_result.returncode != 0:
                self.debug.error(f"Failed to verify FastCGI cache volume creation: {verify_result.stderr}")
                return False
                
            volumes = verify_result.stdout.strip().splitlines()
            if volume_name not in volumes:
                self.debug.error(f"FastCGI cache volume {volume_name} was not created successfully")
                return False
                
            self.debug.info(f"Verified FastCGI cache volume {volume_name} was created successfully")
            return True
        except Exception as e:
            self.debug.error(f"Failed to create FastCGI cache volume: {e}")
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
        Returns True if started successfully or already running, False if error.
        """
        import sys
        try:
            if sys.platform == "darwin":
                # macOS: open Docker Desktop
                result = subprocess.run(["open", "--background", "-a", "Docker"])
                self.debug.info("Started Docker Desktop on macOS.")
                return result.returncode == 0
            elif sys.platform.startswith("linux"):
                # Linux: try systemctl first, fallback to service
                result = subprocess.run(["sudo", "systemctl", "start", "docker"])
                if result.returncode != 0:
                    result = subprocess.run(["sudo", "service", "docker", "start"])
                self.debug.info("Started Docker service on Linux.")
                return result.returncode == 0
            else:
                self.debug.warn("Automatic Docker startup not supported on this operating system.")
                return False
        except Exception as e:
            self.debug.error(f"Error starting Docker: {e}")
            return False
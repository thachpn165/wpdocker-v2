"""
Docker container management.

This module provides the Container class for managing Docker containers.
"""

from python_on_whales import DockerClient
from src.common.logging import Debug, log_call


class Container:
    """Manages a Docker container lifecycle and operations."""
    
    def __init__(self, name: str) -> None:
        """
        Initialize a container manager.
        
        Args:
            name: Name of the Docker container
        """
        self.name = name
        self.debug = Debug("Container")
        self.docker = DockerClient()

    def get(self):
        """
        Get the container object.
        
        Returns:
            Container object or None if not found
        """
        try:
            container = self.docker.container.inspect(self.name)
            return container
        except Exception:
            return None

    def exists(self) -> bool:
        """
        Check if the container exists.
        
        Returns:
            bool: True if container exists, False otherwise
        """
        return self.get() is not None

    @log_call
    def running(self) -> bool:
        """
        Check if the container is running.
        
        Returns:
            bool: True if container is running, False otherwise
        """
        try:
            container = self.get()
            if not container:
                return False
            is_running = container.state.running
            self.debug.debug(f"Container {self.name} state: Running = {is_running}")
            return is_running
        except Exception as e:
            self.debug.error(f"Failed to check container {self.name} state: {e}")
            return False

    def not_running(self) -> bool:
        """
        Check if the container exists but is not running.
        
        Returns:
            bool: True if container exists but not running, False otherwise
        """
        try:
            container = self.get()
            return not container.state.running if container else False
        except Exception as e:
            self.debug.error(f"Failed to check container {self.name} state: {e}")
            return False

    @log_call
    def start(self) -> bool:
        """
        Start the container.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.docker.container.start(self.name)
            self.debug.info(f"Container {self.name} started")
            return True
        except Exception as e:
            self.debug.error(f"Failed to start container {self.name}: {e}")
            return False

    @log_call
    def stop(self) -> bool:
        """
        Stop the container.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.docker.container.stop(self.name)
            self.debug.info(f"Container {self.name} stopped")
            return True
        except Exception as e:
            self.debug.error(f"Failed to stop container {self.name}: {e}")
            return False

    @log_call
    def restart(self) -> bool:
        """
        Restart the container.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.docker.container.restart(self.name)
            self.debug.info(f"Container {self.name} restarted")
            return True
        except Exception as e:
            self.debug.error(f"Failed to restart container {self.name}: {e}")
            return False

    @log_call
    def remove(self, force: bool = True) -> bool:
        """
        Remove the container.
        
        Args:
            force: Force removal even if running
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.docker.container.remove(self.name, force=force)
            self.debug.info(f"Container {self.name} removed")
            return True
        except Exception as e:
            self.debug.error(f"Failed to remove container {self.name}: {e}")
            return False

    @log_call
    def exec(self, cmd, workdir=None, user=None, envs=None):
        """
        Execute a command in the container.
        
        Args:
            cmd: Command to execute
            workdir: Working directory in the container
            user: User to run the command as
            envs: Environment variables
            
        Returns:
            Command output or None if failed
        """
        try:
            exec_result = self.docker.container.execute(
                self.name,
                command=cmd,
                workdir=workdir,
                tty=False,
                interactive=False,
                user=user,
                envs=envs or {}
            )
            self.debug.debug(f"Command output: {exec_result!r}")
            return exec_result
        except Exception as e:
            self.debug.error(f"Command execution failed: {e}")
            return None

    @log_call
    def logs(self, follow=False, tail=100):
        """
        Get container logs.
        
        Args:
            follow: Follow log output
            tail: Number of lines to show from the end
            
        Returns:
            Log output or None if failed
        """
        try:
            logs = self.docker.container.logs(self.name, follow=follow, tail=tail)
            return logs
        except Exception as e:
            self.debug.error(f"Failed to get logs for container {self.name}: {e}")
            return None

    @log_call
    def inspect(self):
        """
        Inspect the container.
        
        Returns:
            Container details or None if failed
        """
        try:
            container = self.docker.container.inspect(self.name)
            self.debug.debug(f"Container {self.name} details: {container}")
            return container
        except Exception as e:
            self.debug.error(f"Failed to inspect container {self.name}: {e}")
            return None

    @log_call
    def copy_to(self, src_path, dest_path_in_container) -> bool:
        """
        Copy file from host to container.
        
        Args:
            src_path: Source path on host
            dest_path_in_container: Destination path in container
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.docker.container.copy(src_path, f"{self.name}:{dest_path_in_container}")
            self.debug.info(f"Copied {src_path} to container {self.name}:{dest_path_in_container}")
            return True
        except Exception as e:
            self.debug.error(f"Failed to copy file to container {self.name}: {e}")
            return False

    @log_call
    def copy_from(self, src_path_in_container, dest_path) -> bool:
        """
        Copy file from container to host.
        
        Args:
            src_path_in_container: Source path in container
            dest_path: Destination path on host
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.docker.container.copy(f"{self.name}:{src_path_in_container}", dest_path)
            self.debug.info(f"Copied {self.name}:{src_path_in_container} to host {dest_path}")
            return True
        except Exception as e:
            self.debug.error(f"Failed to copy file from container {self.name}: {e}")
            return False
"""
Docker container management.

This module provides a Container class for interacting with Docker containers,
including performing operations like starting, stopping, exec, etc.
"""

from typing import Dict, List, Optional, Any, Union
from python_on_whales import DockerClient

from src.common.logging import log_call, debug, info, warn, error


class Container:
    """Class for interacting with Docker containers."""

    def __init__(self, name: str):
        """
        Initialize a container instance.

        Args:
            name: Name of the container
        """
        self.name = name
        self.docker = DockerClient()

    def get(self) -> Optional[Any]:
        """
        Get container info.

        Returns:
            Container object or None if it doesn't exist
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
            True if the container exists, False otherwise
        """
        return self.get() is not None

    @log_call(log_vars=["self.name"])
    def running(self) -> bool:
        """
        Check if the container is running.

        Returns:
            True if the container is running, False otherwise
        """
        try:
            container = self.get()
            if not container:
                return False
            is_running = container.state.running
            debug(f"⚙️ Container {self.name} status: Running = {is_running}")
            return is_running
        except Exception as e:
            error(f"❌ Could not check container {self.name} status: {e}")
            return False

        return {
            "self.name": self.name,
        }

    def not_running(self) -> bool:
        """
        Check if the container is not running.

        Returns:
            True if the container is not running, False otherwise
        """
        try:
            container = self.get()
            return not container.state.running if container else False
        except Exception as e:
            error(f"❌ Could not check container {self.name} status: {e}")
            return False

    @log_call
    def start(self) -> None:
        """Start the container."""
        try:
            self.docker.container.start(self.name)
            info(f"✅ Started container {self.name}.")
        except Exception as e:
            error(f"❌ Error starting container {self.name}: {e}")

    @log_call
    def stop(self) -> None:
        """Stop the container."""
        try:
            self.docker.container.stop(self.name)
            info(f"🛑 Stopped container {self.name}.")
        except Exception as e:
            error(f"❌ Error stopping container {self.name}: {e}")

    @log_call
    def restart(self) -> None:
        """Restart the container."""
        try:
            self.docker.container.restart(self.name)
            info(f"🔄 Restarted container {self.name}.")
        except Exception as e:
            error(f"❌ Error restarting container {self.name}: {e}")

    @log_call
    def remove(self, force: bool = True) -> None:
        """
        Remove the container.

        Args:
            force: Whether to force removal
        """
        try:
            self.docker.container.remove(self.name, force=force)
            info(f"🗑️ Removed container {self.name}.")
        except Exception as e:
            error(f"❌ Error removing container {self.name}: {e}")

    @log_call
    def exec(self, cmd: List[str], workdir: Optional[str] = None,
             user: Optional[str] = None, envs: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Execute a command in the container.

        Args:
            cmd: Command to execute
            workdir: Working directory
            user: User to run the command as
            envs: Environment variables

        Returns:
            Command output or None if it failed
        """
        try:
            # Add user option if provided
            exec_result = self.docker.container.execute(
                self.name,
                command=cmd,
                workdir=workdir,
                tty=False,
                interactive=False,
                user=user,
                envs=envs or {}
            )
            debug(f"📤 Output from container.exec: {exec_result!r}")

            return exec_result
        except Exception as e:
            # Print detailed error from container
            error(f"Error: {e}")
            return None

    @log_call
    def logs(self, follow: bool = False, tail: int = 100) -> Optional[str]:
        """
        Get container logs.

        Args:
            follow: Whether to follow logs
            tail: Number of lines to return

        Returns:
            Container logs or None if it failed
        """
        try:
            logs = self.docker.container.logs(
                self.name, follow=follow, tail=tail)
            return logs
        except Exception as e:
            error(f"❌ Error getting logs for container {self.name}: {e}")
            return None

    @log_call
    def inspect(self) -> Optional[Any]:
        """
        Inspect the container.

        Returns:
            Container inspection data or None if it failed
        """
        try:
            container = self.docker.container.inspect(self.name)
            debug(f"📋 Container {self.name} info: {container}")
            return container
        except Exception as e:
            error(f"❌ Error inspecting container {self.name}: {e}")
            return None

    @log_call
    def copy_to(self, src_path: str, dest_path_in_container: str) -> None:
        """
        Copy a file to the container.

        Args:
            src_path: Source path on the host
            dest_path_in_container: Destination path in the container
        """
        try:
            self.docker.container.copy(
                src_path, f"{self.name}:{dest_path_in_container}")
            info(
                f"📁 Copied {src_path} to container {self.name}:{dest_path_in_container}")
        except Exception as e:
            error(f"❌ Error copying file to container {self.name}: {e}")

    @log_call
    def copy_from(self, src_path_in_container: str, dest_path: str) -> None:
        """
        Copy a file from the container.

        Args:
            src_path_in_container: Source path in the container
            dest_path: Destination path on the host
        """
        try:
            self.docker.container.copy(
                f"{self.name}:{src_path_in_container}", dest_path)
            info(
                f"📁 Copied {self.name}:{src_path_in_container} to host {dest_path}")
        except Exception as e:
            error(f"❌ Error copying file from container {self.name}: {e}")

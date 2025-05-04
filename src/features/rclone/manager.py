"""
Rclone operations and configuration management.

This module provides functionality for managing Rclone operations including
container management, command execution, and file operations.
"""

import os
import subprocess
import json
from typing import Dict, List, Optional, Tuple, Union

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.common.containers.container import Container
from src.common.containers.path_utils import convert_host_path_to_container
from src.features.rclone.config.manager import RcloneConfigManager


class RcloneManager:
    """Manages Rclone operations and configuration."""
    
    _instance = None
    
    def __new__(cls) -> 'RcloneManager':
        """
        Singleton pattern to ensure only one instance exists.
        
        Returns:
            RcloneManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(RcloneManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the Rclone manager."""
        if self._initialized:
            return
            
        self._initialized = True
        self.debug = Debug("RcloneManager")
        
        # Docker container management
        self.container_name = env.get("RCLONE_CONTAINER_NAME", "wpdocker_rclone")
        self.container = Container(self.container_name)
        
        # Configuration paths
        self.config_dir = os.path.join(env["CONFIG_DIR"], "rclone")
        self.config_file = os.path.join(self.config_dir, "rclone.conf")
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
    
    @log_call
    def is_container_running(self) -> bool:
        """
        Check if the Rclone container is running.
        
        Returns:
            bool: True if the container is running, False otherwise
        """
        return self.container.running()
    
    @log_call
    def start_container(self) -> bool:
        """
        Start the Rclone container.
        
        Returns:
            bool: True if the container was started successfully, False otherwise
        """
        return self.container.start()
    
    @log_call
    def stop_container(self) -> bool:
        """
        Stop the Rclone container.
        
        Returns:
            bool: True if the container was stopped successfully, False otherwise
        """
        return self.container.stop()
    
    @log_call
    def restart_container(self) -> bool:
        """
        Restart the Rclone container.
        
        Returns:
            bool: True if the container was restarted successfully, False otherwise
        """
        return self.container.restart()
    
    @log_call
    def execute_command(self, command: List[str], capture_output: bool = True) -> Tuple[bool, str]:
        """
        Execute an Rclone command in the container.
        
        Args:
            command: Command arguments to execute
            capture_output: Whether to capture command output
            
        Returns:
            Tuple of (success, output)
        """
        if not self.is_container_running():
            if not self.start_container():
                return False, "Failed to start Rclone container"
        
        # Prepend 'rclone' to the command if it's not already there
        if command and command[0] != "rclone":
            command = ["rclone"] + command
            
        # Execute the command inside the container
        full_command = ["docker", "exec", self.container_name] + command
        self.debug.info(f"Executing command: {' '.join(full_command)}")
        
        try:
            if capture_output:
                result = subprocess.run(
                    full_command, 
                    check=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                return True, result.stdout
            else:
                subprocess.run(full_command, check=True)
                return True, "Command executed successfully"
        except subprocess.CalledProcessError as e:
            self.debug.error(f"Command failed: {e}")
            error_message = e.stderr if hasattr(e, 'stderr') else str(e)
            return False, error_message
    
    @log_call
    def list_remotes(self) -> List[str]:
        """
        List configured remotes.
        
        Returns:
            List[str]: List of remote names
        """
        success, output = self.execute_command(["listremotes"])
        if success:
            # Remove trailing colons and empty lines
            remotes = [line.rstrip(':') for line in output.splitlines() if line.strip()]
            return remotes
        return []
    
    @log_call
    def add_remote(self, name: str, remote_type: str, params: Dict[str, str]) -> bool:
        """
        Add a new remote configuration.
        
        Args:
            name: Name of the remote
            remote_type: Type of remote (s3, drive, etc.)
            params: Configuration parameters
            
        Returns:
            bool: True if remote was added successfully, False otherwise
        """
        # Check if params contain a manual configuration (for OAuth providers)
        if "token" in params and remote_type in ["drive", "dropbox", "onedrive", "box", "mega", "pcloud"]:
            # Use ConfigManager to add directly to the config file
            config = RcloneConfigManager()
            params["type"] = remote_type  # Add type to params
            success = config.add_remote(name, params)
            
            if success:
                self.debug.info(f"Added remote '{name}' directly to config file")
                return True
            else:
                self.debug.error(f"Failed to add remote '{name}' to config file")
                return False
        else:
            # Use the traditional method via rclone command
            command = ["config", "create", name, remote_type]
            for key, value in params.items():
                command.extend([f"{key}={value}"])
            
            success, output = self.execute_command(command)
            return success
    
    @log_call
    def remove_remote(self, name: str) -> bool:
        """
        Remove a remote configuration.
        
        Args:
            name: Name of the remote to remove
            
        Returns:
            bool: True if remote was removed successfully, False otherwise
        """
        success, _ = self.execute_command(["config", "delete", name])
        return success
    
    @log_call
    def sync(self, source: str, destination: str, flags: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Sync from source to destination.
        
        Args:
            source: Source path
            destination: Destination path
            flags: Optional command flags
            
        Returns:
            Tuple of (success, output)
        """
        command = ["sync", source, destination]
        if flags:
            command.extend(flags)
        
        return self.execute_command(command)
    
    @log_call
    def get_backup_dir_for_domain(self, domain: Optional[str] = None) -> str:
        """
        Get backup directory for specific domain or global backup directory.
        
        Args:
            domain: The domain name for site-specific backup
            
        Returns:
            str: Path to backup directory
        """
        if domain:
            # Site-specific backup directory
            backup_dir = os.path.join(env["SITES_DIR"], domain, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            return backup_dir
        else:
            # Global backup directory
            backup_dir = os.path.join(env["INSTALL_DIR"], "backups")
            os.makedirs(backup_dir, exist_ok=True)
            return backup_dir
            
    @log_call
    def backup(self, source: str, remote: str, destination_path: str, 
              domain: Optional[str] = None, flags: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Backup a local directory to a remote destination.
        
        Args:
            source: Source path to backup
            remote: Remote storage name
            destination_path: Path on remote storage
            domain: Optional domain name for site-specific backup
            flags: Optional command flags
            
        Returns:
            Tuple of (success, output)
        """
        # If source is relative, convert to absolute path based on domain
        if not os.path.isabs(source):
            if domain:
                # Use site-specific backup directory
                source = os.path.join(self.get_backup_dir_for_domain(domain), source)
            else:
                # Use global backup directory
                source = os.path.join(self.get_backup_dir_for_domain(), source)
        
        # Convert host path to container path
        container_source = convert_host_path_to_container(source, 'rclone')
        
        # Ensure the remote destination format is correct
        if not remote.endswith(':'):
            remote = f"{remote}:"
        
        destination = f"{remote}{destination_path}"
        
        # Default flags for backup operations if not provided
        if flags is None:
            flags = ["--progress", "--transfers", "4"]
        
        self.debug.info(f"Backup source (host): {source}")
        self.debug.info(f"Backup source (container): {container_source}")
        self.debug.info(f"Backup destination: {destination}")
        
        # Use container path instead of host path
        source = container_source
        
        # Check if source is a directory or file
        is_directory = os.path.isdir(source)
        
        # Create remote directory structure first
        remote_dir = os.path.dirname(destination)
        if remote_dir:  # Only create directories if there's a directory part in the path
            # Break path into components as mkdir doesn't support -p
            remote_components = remote_dir.split(':')
            if len(remote_components) > 1:  # Has remote: prefix
                remote_prefix = f"{remote_components[0]}:"
                path_parts = remote_components[1].split('/')
                current_path = ""
                
                for component in path_parts:
                    if component:
                        current_path = f"{current_path}/{component}" if current_path else component
                        mkdir_success, mkdir_message = self.execute_command(
                            ["mkdir", f"{remote_prefix}{current_path}"]
                        )
                        # Don't show a warning if the directory already exists
                        if not mkdir_success and "already exists" not in mkdir_message.lower():
                            self.debug.warn(f"Unable to create directory '{current_path}': {mkdir_message}")
        
        # Use sync for directories, copy for single files
        if is_directory:
            return self.sync(source, destination, flags)
        else:
            return self.execute_command(["copy", source, destination] + (flags or []))
    
    @log_call
    def restore(self, remote: str, source_path: str, local_destination: str, 
               domain: Optional[str] = None, flags: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Restore from a remote source to a local destination.
        
        Args:
            remote: Remote storage name
            source_path: Path on remote storage
            local_destination: Local destination path
            domain: Optional domain name for site-specific restore
            flags: Optional command flags
            
        Returns:
            Tuple of (success, output)
        """
        # Ensure the remote source format is correct
        if not remote.endswith(':'):
            remote = f"{remote}:"
            
        source = f"{remote}{source_path}"
        
        # If destination is relative, convert to absolute path based on domain
        if not os.path.isabs(local_destination):
            if domain:
                # Use site-specific backup directory
                local_destination = os.path.join(self.get_backup_dir_for_domain(domain), local_destination)
            else:
                # Use global backup directory
                local_destination = os.path.join(self.get_backup_dir_for_domain(), local_destination)
        
        # Ensure destination directory exists
        os.makedirs(os.path.dirname(local_destination), exist_ok=True)
        
        # Default flags for restore operations if not provided
        if flags is None:
            flags = ["--progress", "--transfers", "4"]
        
        # Convert the local destination to container path
        container_destination = convert_host_path_to_container(local_destination, 'rclone')
        
        self.debug.info(f"Restore source: {source}")
        self.debug.info(f"Restore destination (host): {local_destination}")
        self.debug.info(f"Restore destination (container): {container_destination}")
        
        # Use container path instead of host path
        local_destination = container_destination
        
        # Check if source is a directory or single file by trying to list it
        try:
            list_result = self.list_files(remote, source_path)
            is_directory = len(list_result) > 0
        except Exception:
            # If list fails, assume it's a single file
            is_directory = False
        
        # Use sync for directories, copy for single files
        if is_directory:
            return self.sync(source, local_destination, flags)
        else:
            return self.execute_command(["copy", source, local_destination] + (flags or []))
    
    @log_call
    def list_files(self, remote: str, path: str = "") -> List[Dict[str, Union[str, int]]]:
        """
        List files in a remote path.
        
        Args:
            remote: Remote storage name
            path: Path on remote storage
            
        Returns:
            List[Dict]: List of file information dictionaries
        """
        # Ensure the remote format is correct
        if not remote.endswith(':'):
            remote = f"{remote}:"
            
        remote_path = f"{remote}{path}"
        
        success, output = self.execute_command(["lsjson", remote_path])
        if success:
            try:
                files = json.loads(output)
                return files
            except json.JSONDecodeError:
                self.debug.error(f"Failed to parse JSON output: {output}")
                return []
        return []
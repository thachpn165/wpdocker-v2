"""
Rclone configuration management.

This module provides functionality for managing Rclone configuration file,
including reading, writing, and manipulating remote configurations.
"""

import os
import configparser
from typing import Dict, List, Optional, Tuple

from src.common.logging import Debug, log_call
from src.common.utils.environment import env


class RcloneConfigManager:
    """Manages Rclone configuration file."""
    
    _instance = None
    
    def __new__(cls) -> 'RcloneConfigManager':
        """
        Singleton pattern to ensure only one instance exists.
        
        Returns:
            RcloneConfigManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(RcloneConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the Rclone configuration manager."""
        if self._initialized:
            return
            
        self._initialized = True
        self.debug = Debug("RcloneConfigManager")
        
        # Configuration paths - use environment variables if available
        self.config_dir = env.get("RCLONE_CONFIG_DIR", os.path.join(env["CONFIG_DIR"], "rclone"))
        self.config_file = env.get("RCLONE_CONFIG_FILE", os.path.join(self.config_dir, "rclone.conf"))
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Create config file if it doesn't exist
        if not os.path.exists(self.config_file):
            with open(self.config_file, "w") as f:
                pass
                
        # Debug output to help with troubleshooting
        self.debug.info(f"Using Rclone config file: {self.config_file}")
    
    @log_call
    def read_config(self) -> configparser.ConfigParser:
        """
        Read the Rclone configuration file.
        
        Returns:
            configparser.ConfigParser: Parsed config file
        """
        config = configparser.ConfigParser()
        config.read(self.config_file)
        return config
    
    @log_call
    def write_config(self, config: configparser.ConfigParser) -> bool:
        """
        Write to the Rclone configuration file.
        
        Args:
            config: ConfigParser object to write
            
        Returns:
            bool: True if write was successful, False otherwise
        """
        try:
            with open(self.config_file, "w") as f:
                config.write(f)
            return True
        except Exception as e:
            self.debug.error(f"Failed to write config: {e}")
            return False
    
    @log_call
    def get_remotes(self) -> List[str]:
        """
        Get a list of configured remotes.
        
        Returns:
            List[str]: List of remote names
        """
        config = self.read_config()
        return config.sections()
    
    @log_call
    def get_remote_config(self, remote_name: str) -> Optional[Dict[str, str]]:
        """
        Get the configuration for a specific remote.
        
        Args:
            remote_name: Name of the remote
            
        Returns:
            Optional[Dict[str, str]]: Remote configuration or None if not found
        """
        config = self.read_config()
        if remote_name in config:
            return dict(config[remote_name])
        return None
    
    @log_call
    def add_remote(self, remote_name: str, remote_config: Dict[str, str]) -> bool:
        """
        Add a new remote configuration.
        
        Args:
            remote_name: Name of the remote
            remote_config: Remote configuration parameters
            
        Returns:
            bool: True if remote was added successfully, False otherwise
        """
        config = self.read_config()
        if remote_name in config:
            self.debug.warn(f"Remote '{remote_name}' already exists, updating configuration")
        
        config[remote_name] = remote_config
        return self.write_config(config)
    
    @log_call
    def remove_remote(self, remote_name: str) -> bool:
        """
        Remove a remote configuration.
        
        Args:
            remote_name: Name of the remote to remove
            
        Returns:
            bool: True if remote was removed successfully, False otherwise
        """
        config = self.read_config()
        if remote_name not in config:
            self.debug.warn(f"Remote '{remote_name}' does not exist")
            return False
        
        config.remove_section(remote_name)
        return self.write_config(config)
    
    @log_call
    def update_remote(self, remote_name: str, key: str, value: str) -> bool:
        """
        Update a specific key in a remote configuration.
        
        Args:
            remote_name: Name of the remote
            key: Configuration key to update
            value: New value for the key
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        config = self.read_config()
        if remote_name not in config:
            self.debug.error(f"Remote '{remote_name}' does not exist")
            return False
        
        config[remote_name][key] = value
        return self.write_config(config)
    
    @log_call
    def backup_config(self, backup_suffix: str = "backup") -> Tuple[bool, str]:
        """
        Create a backup of the current configuration.
        
        Args:
            backup_suffix: Suffix to append to the backup filename
            
        Returns:
            Tuple[bool, str]: (success, backup_file_path) if successful,
                             (False, error_message) otherwise
        """
        backup_file = f"{self.config_file}.{backup_suffix}"
        try:
            with open(self.config_file, "r") as src, open(backup_file, "w") as dst:
                dst.write(src.read())
            return True, backup_file
        except Exception as e:
            self.debug.error(f"Failed to backup config: {e}")
            return False, str(e)
    
    @log_call
    def restore_config(self, backup_file: str) -> bool:
        """
        Restore configuration from a backup file.
        
        Args:
            backup_file: Path to the backup file
            
        Returns:
            bool: True if restoration was successful, False otherwise
        """
        try:
            with open(backup_file, "r") as src, open(self.config_file, "w") as dst:
                dst.write(src.read())
            return True
        except Exception as e:
            self.debug.error(f"Failed to restore config: {e}")
            return False
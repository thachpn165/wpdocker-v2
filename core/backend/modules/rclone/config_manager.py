#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import configparser
from typing import Dict, List, Optional, Tuple

from core.backend.utils.env_utils import get_env_value
from core.backend.utils.debug import Debug


class RcloneConfigManager:
    """Manages Rclone configuration file."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(RcloneConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the Rclone configuration manager."""
        if self._initialized:
            return
            
        self._initialized = True
        self.debug = Debug("RcloneConfigManager")
        
        # Configuration paths
        self.config_dir = os.path.join(get_env_value("CONFIG_DIR"), "rclone")
        self.config_file = os.path.join(self.config_dir, "rclone.conf")
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Create config file if it doesn't exist
        if not os.path.exists(self.config_file):
            with open(self.config_file, "w") as f:
                pass
    
    def read_config(self) -> configparser.ConfigParser:
        """Read the Rclone configuration file."""
        config = configparser.ConfigParser()
        config.read(self.config_file)
        return config
    
    def write_config(self, config: configparser.ConfigParser) -> bool:
        """Write to the Rclone configuration file."""
        try:
            with open(self.config_file, "w") as f:
                config.write(f)
            return True
        except Exception as e:
            self.debug.error(f"Failed to write config: {e}")
            return False
    
    def get_remotes(self) -> List[str]:
        """Get a list of configured remotes."""
        config = self.read_config()
        return config.sections()
    
    def get_remote_config(self, remote_name: str) -> Optional[Dict[str, str]]:
        """Get the configuration for a specific remote."""
        config = self.read_config()
        if remote_name in config:
            return dict(config[remote_name])
        return None
    
    def add_remote(self, remote_name: str, remote_config: Dict[str, str]) -> bool:
        """Add a new remote configuration."""
        config = self.read_config()
        if remote_name in config:
            self.debug.warn(f"Remote '{remote_name}' already exists, updating configuration")
        
        config[remote_name] = remote_config
        return self.write_config(config)
    
    def remove_remote(self, remote_name: str) -> bool:
        """Remove a remote configuration."""
        config = self.read_config()
        if remote_name not in config:
            self.debug.warn(f"Remote '{remote_name}' does not exist")
            return False
        
        config.remove_section(remote_name)
        return self.write_config(config)
    
    def update_remote(self, remote_name: str, key: str, value: str) -> bool:
        """Update a specific key in a remote configuration."""
        config = self.read_config()
        if remote_name not in config:
            self.debug.error(f"Remote '{remote_name}' does not exist")
            return False
        
        config[remote_name][key] = value
        return self.write_config(config)
    
    def backup_config(self, backup_suffix: str = "backup") -> Tuple[bool, str]:
        """Create a backup of the current configuration."""
        backup_file = f"{self.config_file}.{backup_suffix}"
        try:
            with open(self.config_file, "r") as src, open(backup_file, "w") as dst:
                dst.write(src.read())
            return True, backup_file
        except Exception as e:
            self.debug.error(f"Failed to backup config: {e}")
            return False, str(e)
    
    def restore_config(self, backup_file: str) -> bool:
        """Restore configuration from a backup file."""
        try:
            with open(backup_file, "r") as src, open(self.config_file, "w") as dst:
                dst.write(src.read())
            return True
        except Exception as e:
            self.debug.error(f"Failed to restore config: {e}")
            return False
"""
MySQL configuration editing functionality.

This module provides functions for editing MySQL server configuration
and restarting the service to apply changes.
"""

import os
import subprocess
from typing import Optional, Dict, Any

from src.common.logging import log_call, info, error, debug
from src.common.utils.environment import env_required, env
from src.common.utils.editor import choose_editor
from src.common.containers.container import Container


# Ensure required environment variables are set
env_required(["MYSQL_CONFIG_FILE", "MYSQL_CONTAINER_NAME"])


@log_call
def edit_mysql_config() -> bool:
    """
    Open MySQL configuration file in an editor and restart MySQL after editing.
    
    This function allows the user to edit the MySQL server configuration file
    using their preferred text editor, then restarts the MySQL container to
    apply the changes.
    
    Returns:
        bool: True if edit was successful, False otherwise
    """
    config_path = env["MYSQL_CONFIG_FILE"]

    # Ensure directory exists
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        try:
            info(f"Creating MySQL config directory: {config_dir}")
            os.makedirs(config_dir, exist_ok=True)
        except Exception as e:
            error(f"❌ Failed to create MySQL config directory: {e}")
            return False

    # Create empty config file if it doesn't exist
    if not os.path.isfile(config_path):
        try:
            info(f"Creating empty MySQL config file: {config_path}")
            with open(config_path, "w") as f:
                f.write("[mysqld]\n# MySQL server configuration\n")
        except Exception as e:
            error(f"❌ Failed to create MySQL config file: {e}")
            return False

    editor = choose_editor()
    if not editor:
        error("❌ No text editor selected.")
        return False

    try:
        # Open the configuration file in the selected editor
        subprocess.run([editor, config_path], check=True)
        
        # Restart the MySQL container to apply changes
        container = Container(env["MYSQL_CONTAINER_NAME"])
        container.restart()
        info("🔁 Restarted MySQL container to apply configuration changes.")
        return True
    except Exception as e:
        error(f"❌ Error editing MySQL configuration: {e}")
        return False


@log_call
def backup_mysql_config() -> Optional[str]:
    """
    Create a backup of the MySQL configuration file.
    
    Returns:
        Optional[str]: Path to the backup file if successful, None otherwise
    """
    config_path = env["MYSQL_CONFIG_FILE"]
    
    # Ensure directory exists
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        try:
            info(f"Creating MySQL config directory: {config_dir}")
            os.makedirs(config_dir, exist_ok=True)
        except Exception as e:
            error(f"❌ Failed to create MySQL config directory: {e}")
            return None
    
    if not os.path.isfile(config_path):
        error(f"❌ MySQL configuration file not found: {config_path}")
        return None
    
    backup_path = f"{config_path}.bak"
    try:
        with open(config_path, 'r') as src:
            with open(backup_path, 'w') as dst:
                dst.write(src.read())
        info(f"✅ MySQL configuration backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        error(f"❌ Error backing up MySQL configuration: {e}")
        return None


@log_call
def restore_mysql_config(backup_path: Optional[str] = None) -> bool:
    """
    Restore MySQL configuration from backup.
    
    Args:
        backup_path: Path to the backup file to restore, or None to use default
        
    Returns:
        bool: True if restore was successful, False otherwise
    """
    config_path = env["MYSQL_CONFIG_FILE"]
    backup_path = backup_path or f"{config_path}.bak"
    
    # Ensure directory exists
    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        try:
            info(f"Creating MySQL config directory: {config_dir}")
            os.makedirs(config_dir, exist_ok=True)
        except Exception as e:
            error(f"❌ Failed to create MySQL config directory: {e}")
            return False
    
    if not os.path.isfile(backup_path):
        error(f"❌ MySQL configuration backup not found: {backup_path}")
        return False
    
    try:
        with open(backup_path, 'r') as src:
            with open(config_path, 'w') as dst:
                dst.write(src.read())
        
        # Restart the MySQL container to apply changes
        container = Container(env["MYSQL_CONTAINER_NAME"])
        container.restart()
        info("✅ MySQL configuration restored from backup and service restarted.")
        return True
    except Exception as e:
        error(f"❌ Error restoring MySQL configuration: {e}")
        return False
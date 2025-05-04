"""
Environment file updater for migration to new structure.

This module provides utilities for updating the core.env file to use
the new directory structure.
"""

import os
import re
from typing import Dict, List, Tuple, Optional

from src.common.logging import Debug, log_call
from src.core.migration.path_mapping import ENV_VAR_CHANGES


class EnvUpdater:
    """Handles updating environment variables to use the new directory structure."""
    
    def __init__(self) -> None:
        """Initialize the environment updater."""
        self.debug = Debug("EnvUpdater")
        
    @log_call
    def update_env_file(self, env_file: str) -> bool:
        """
        Update paths in an environment file.
        
        Args:
            env_file: Path to environment file
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            # Read the env file
            with open(env_file, "r") as f:
                lines = f.readlines()
                
            # Update the lines
            updated_lines = self._update_env_lines(lines)
            
            # Write updated content
            with open(env_file, "w") as f:
                f.writelines(updated_lines)
                
            self.debug.success(f"Updated environment file: {env_file}")
            return True
        except Exception as e:
            self.debug.error(f"Failed to update environment file {env_file}: {e}")
            return False
            
    def _update_env_lines(self, lines: List[str]) -> List[str]:
        """
        Update directory paths in environment file lines.
        
        Args:
            lines: Original environment file lines
            
        Returns:
            Updated environment file lines
        """
        updated_lines = []
        
        for line in lines:
            # Skip comments and empty lines
            if line.strip().startswith("#") or not line.strip():
                updated_lines.append(line)
                continue
                
            # Check if line defines a directory
            if "=" in line:
                var_name, value = line.strip().split("=", 1)
                var_name = var_name.strip()
                
                if var_name in ENV_VAR_CHANGES:
                    # Extract the base path if it's using $INSTALL_DIR
                    install_dir_match = re.match(r'.*\$INSTALL_DIR/(.*)$', value.strip('"\''))
                    if install_dir_match:
                        base_path = install_dir_match.group(1)
                        # Replace with new path
                        new_value = f'"$INSTALL_DIR/{ENV_VAR_CHANGES[var_name]}"'
                        updated_lines.append(f"{var_name}={new_value}\n")
                    else:
                        # Not using $INSTALL_DIR, just update the path
                        if value.endswith("/core/templates"):
                            new_value = value.replace("/core/templates", "/src/templates")
                            updated_lines.append(f"{var_name}={new_value}\n")
                        elif value.endswith("/core/bash-utils"):
                            new_value = value.replace("/core/bash-utils", "/src/bash")
                            updated_lines.append(f"{var_name}={new_value}\n")
                        elif value.endswith("/core/wp"):
                            new_value = value.replace("/core/wp", "/src/wordpress")
                            updated_lines.append(f"{var_name}={new_value}\n")
                        else:
                            updated_lines.append(line)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
                
        return updated_lines


# Singleton instance
env_updater = EnvUpdater()

@log_call
def update_env_file(env_file: str) -> bool:
    """
    Update paths in an environment file.
    
    Args:
        env_file: Path to environment file
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    return env_updater.update_env_file(env_file)
"""
Script updater for migration to new structure.

This module provides utilities for updating shell scripts to use
the new directory structure.
"""

import os
import re
import glob
from typing import List, Dict, Set

from src.common.logging import Debug, log_call
from src.core.migration.path_mapping import ENV_VAR_CHANGES


class ScriptUpdater:
    """Handles updating shell scripts to use the new directory structure."""
    
    def __init__(self) -> None:
        """Initialize the script updater."""
        self.debug = Debug("ScriptUpdater")
        
    @log_call
    def update_scripts(self, scripts_dir: str) -> Dict[str, bool]:
        """
        Update all shell scripts in a directory.
        
        Args:
            scripts_dir: Directory containing shell scripts
            
        Returns:
            Dict mapping script paths to update success status
        """
        script_files = self._find_shell_scripts(scripts_dir)
        results = {}
        
        self.debug.info(f"Found {len(script_files)} shell scripts to update")
        for script_file in script_files:
            self.debug.info(f"Updating script: {script_file}")
            success = self._update_script(script_file)
            results[script_file] = success
            
        return results
        
    def _find_shell_scripts(self, scripts_dir: str) -> List[str]:
        """
        Find all shell scripts in a directory.
        
        Args:
            scripts_dir: Directory to search
            
        Returns:
            List of script file paths
        """
        sh_files = glob.glob(os.path.join(scripts_dir, "**/*.sh"), recursive=True)
        return sh_files
        
    @log_call
    def _update_script(self, script_path: str) -> bool:
        """
        Update a single shell script.
        
        Args:
            script_path: Path to shell script
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        try:
            # Read the script
            with open(script_path, "r") as f:
                content = f.read()
                
            # Update paths
            updated_content = self._update_paths(content)
            
            # Write updated script
            with open(script_path, "w") as f:
                f.write(updated_content)
                
            return True
        except Exception as e:
            self.debug.error(f"Failed to update script {script_path}: {e}")
            return False
            
    def _update_paths(self, content: str) -> str:
        """
        Update paths in script content.
        
        Args:
            content: Original script content
            
        Returns:
            Updated script content
        """
        updated_content = content
        
        # Update env var references
        for old_var, new_path in ENV_VAR_CHANGES.items():
            # Update direct path references with $variable
            pattern = f'\\${{{old_var}}}'
            updated_content = re.sub(pattern, f'$INSTALL_DIR/{new_path}', updated_content)
            
            # Update directory assignments
            dir_pattern = f'{old_var}="[^"]*"'
            updated_content = re.sub(dir_pattern, f'{old_var}="$INSTALL_DIR/{new_path}"', updated_content)
            
        # Update direct path references
        updated_content = updated_content.replace('core/templates', 'src/templates')
        updated_content = updated_content.replace('core/bash-utils', 'src/bash')
        updated_content = updated_content.replace('core/wp', 'src/wordpress')
        
        return updated_content


# Singleton instance
script_updater = ScriptUpdater()

@log_call
def update_scripts(scripts_dir: str) -> Dict[str, bool]:
    """
    Update all shell scripts in a directory.
    
    Args:
        scripts_dir: Directory containing shell scripts
        
    Returns:
        Dict mapping script paths to update success status
    """
    return script_updater.update_scripts(scripts_dir)
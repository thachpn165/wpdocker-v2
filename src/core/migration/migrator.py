"""
Migration tool for transitioning from old structure to new structure.

This module provides a comprehensive tool for migrating from the old
directory structure to the new refactored structure.
"""

import os
import shutil
import sys
from typing import Dict, List, Optional, Tuple

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.core.migration.path_mapping import (
    OLD_TO_NEW_PATHS, 
    get_new_path
)
from src.core.migration.script_updater import update_scripts
from src.core.migration.env_updater import update_env_file


class StructureMigrator:
    """
    Handles the migration from old directory structure to new structure.
    
    This class implements a Facade pattern to provide a simplified interface
    for the entire migration process.
    """
    
    def __init__(self) -> None:
        """Initialize the structure migrator."""
        self.debug = Debug("StructureMigrator")
        self.install_dir = env.get("INSTALL_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
        
    @log_call
    def migrate(self) -> bool:
        """
        Perform the complete migration process.
        
        Returns:
            bool: True if migration was successful, False otherwise
        """
        self.debug.info("Starting migration from old structure to new structure")
        
        # Step 1: Update environment file
        env_file = os.path.join(self.install_dir, "src", "config", "core.env")
        if not update_env_file(env_file):
            self.debug.error("Failed to update environment file")
            return False
            
        # Step 2: Update scripts
        scripts_dir = os.path.join(self.install_dir, "scripts")
        if os.path.exists(scripts_dir):
            script_results = update_scripts(scripts_dir)
            failed_scripts = [path for path, success in script_results.items() if not success]
            if failed_scripts:
                self.debug.warn(f"Failed to update {len(failed_scripts)} scripts")
                
        # Step 3: Print migration summary
        self._print_migration_summary()
        
        self.debug.success("Migration completed successfully")
        return True
        
    def _print_migration_summary(self) -> None:
        """Print a summary of the migration process."""
        self.debug.info("Migration summary:")
        
        # Template files
        template_dir = os.path.join(self.install_dir, "src", "templates")
        template_count = self._count_files(template_dir)
        self.debug.info(f"- {template_count} template files migrated")
        
        # Bash utils
        bash_dir = os.path.join(self.install_dir, "src", "bash")
        bash_count = self._count_files(bash_dir)
        self.debug.info(f"- {bash_count} bash utility files migrated")
        
        # WordPress files
        wp_dir = os.path.join(self.install_dir, "src", "wordpress")
        wp_count = self._count_files(wp_dir)
        self.debug.info(f"- {wp_count} WordPress files migrated")
        
        # Configuration files
        config_dir = os.path.join(self.install_dir, "src", "config")
        config_count = self._count_files(config_dir)
        self.debug.info(f"- {config_count} configuration files migrated")
        
        # Total path mappings
        self.debug.info(f"- {len(OLD_TO_NEW_PATHS)} path mappings defined")
        
    def _count_files(self, directory: str) -> int:
        """
        Count files in a directory recursively.
        
        Args:
            directory: Directory path
            
        Returns:
            Number of files
        """
        count = 0
        if os.path.exists(directory):
            for root, _, files in os.walk(directory):
                count += len(files)
        return count


# Main entry point for migration
@log_call
def migrate_structure() -> bool:
    """
    Perform the migration from old structure to new structure.
    
    Returns:
        bool: True if migration was successful, False otherwise
    """
    migrator = StructureMigrator()
    return migrator.migrate()
    
    
if __name__ == "__main__":
    success = migrate_structure()
    sys.exit(0 if success else 1)
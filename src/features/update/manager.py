"""
Update manager for WP Docker.

This module provides a central manager for update operations,
including checking for and applying updates.
"""

import os
from typing import Dict, Optional, Tuple, Any, Union

from src.common.logging import Debug, log_call


class UpdateManager:
    """
    Central manager for update operations.

    This class provides a unified interface for update operations,
    handling different update mechanisms (package or git-based) depending
    on the installation method.
    """
    
    _instance = None
    
    def __new__(cls) -> 'UpdateManager':
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(UpdateManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self) -> None:
        """Initialize the update manager."""
        if self._initialized:
            return
            
        self._initialized = True
        self.debug = Debug("UpdateManager")
        
        # Lazy-load updaters to avoid circular imports
        self._package_updater = None
        self._git_updater = None
        
    def _get_package_updater(self):
        """Get or create the package updater."""
        if self._package_updater is None:
            from src.features.update.core.package_updater import PackageUpdater
            self._package_updater = PackageUpdater()
        return self._package_updater
        
    def _get_git_updater(self):
        """Get or create the git updater."""
        if self._git_updater is None:
            from src.features.update.core.git_updater import GitUpdater
            self._git_updater = GitUpdater()
        return self._git_updater
    
    @log_call
    def is_git_installation(self) -> bool:
        """
        Check if this is a git-based installation.
        
        Returns:
            bool: True if this is a git installation, False otherwise
        """
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.exists(os.path.join(project_root, ".git"))
    
    @log_call
    def get_current_version(self) -> Tuple[str, str]:
        """
        Get the current version and channel.
        
        Returns:
            Tuple of (version, channel)
        """
        from src.version import VERSION, CHANNEL
        return VERSION, CHANNEL
        
    @log_call
    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """
        Check for available updates.
        
        Returns:
            Dict with update information or None if no updates are available
        """
        _, channel = self.get_current_version()
        
        if channel == "dev":
            self.debug.info("Dev channel does not support automatic updates")
            return None
            
        if self.is_git_installation():
            self.debug.info("Using git-based update checker")
            return self._get_git_updater().check_for_updates()
        else:
            self.debug.info("Using package-based update checker")
            return self._get_package_updater().check_for_updates()
            
    @log_call
    def update(self) -> bool:
        """
        Apply available updates.
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        _, channel = self.get_current_version()
        
        if channel == "dev":
            self.debug.info("Dev channel does not support automatic updates")
            return False
            
        if self.is_git_installation():
            self.debug.info("Using git-based updater")
            return self._get_git_updater().update()
        else:
            self.debug.info("Using package-based updater")
            update_info = self._get_package_updater().check_for_updates()
            if update_info:
                return self._get_package_updater().download_and_install_update(update_info)
            return False
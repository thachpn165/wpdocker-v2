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

    This class provides a unified interface for update operations
    using the VersionUpdater as the implementation.
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
        self._version_updater = None

    def _get_version_updater(self):
        """Get or create the version updater."""
        if self._version_updater is None:
            from src.features.update.core.version_updater import version_updater
            self._version_updater = version_updater
        return self._version_updater

    @log_call
    def get_current_version(self) -> Tuple[str, str]:
        """
        Get the current version and channel.

        Returns:
            Tuple of (version, channel)
        """
        from src.common.utils.version_helper import get_version, get_channel
        return get_version(), get_channel()

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

        # Using the VersionUpdater implementation
        return self._get_version_updater().check_for_updates()

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

        # First check for updates
        update_info = self.check_for_updates()
        if not update_info:
            self.debug.info("No updates available")
            return False

        # Using the VersionUpdater implementation
        return self._get_version_updater().download_and_install(update_info)
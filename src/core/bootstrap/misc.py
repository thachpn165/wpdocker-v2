"""
Miscellaneous bootstrap module.

This module handles various small initialization tasks that don't fit
in any other bootstrap module.
"""

import os

from src.common.logging import Debug, log_call
from src.common.utils.environment import env
from src.core.bootstrap.base import BaseBootstrap
from src.core.utils.downloader import Downloader
from src.common.utils.validation import validate_directory


@log_call
class MiscBootstrap(BaseBootstrap):
    debug = Debug("MiscBootstrap")
    """Handles miscellaneous initialization tasks."""

    def __init__(self) -> None:
        """Initialize miscellaneous bootstrap."""
        super().__init__("MiscBootstrap")

    def is_bootstrapped(self) -> bool:
        """
        Check if miscellaneous components are already bootstrapped.

        Returns:
            bool: True if all components are bootstrapped, False otherwise
        """
        # Check if WP-CLI exists
        wp_cli_path = os.path.join(env["WORDPRESS_DIR"], "wp-cli.phar")
        if not os.path.isfile(wp_cli_path):
            return False

        return True

    @log_call
    def check_prerequisites(self) -> bool:
        """
        Check if prerequisites for miscellaneous bootstrap are met.

        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        required_env_vars = [
            "INSTALL_DIR",
            "WORDPRESS_DIR"
        ]

        for var in required_env_vars:
            if var not in env:
                self.debug.error(f"Required environment variable not set: {var}")
                return False

        return True

    @log_call
    def execute_bootstrap(self) -> bool:
        """
        Execute the miscellaneous bootstrap process.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure WP-CLI exists
            if not self._ensure_wp_cli():
                return False

            self.debug.success("Miscellaneous bootstrap completed successfully")
            return True
        except Exception as e:
            self.debug.error(f"Failed to bootstrap miscellaneous components: {e}")
            return False

    def mark_bootstrapped(self) -> None:
        """Mark miscellaneous components as bootstrapped."""
        # Miscellaneous bootstrap is marked by the presence of its files
        pass

    @log_call
    def _ensure_wp_cli(self) -> bool:
        """
        Ensure WordPress CLI exists and is executable.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            wp_cli_path = os.path.join(env["WORDPRESS_DIR"], "wp-cli.phar")

            # Skip if WP-CLI already exists
            if os.path.isfile(wp_cli_path):
                self.debug.debug(f"WordPress CLI already exists: {wp_cli_path}")

                # Make sure it's executable
                os.chmod(wp_cli_path, 0o755)
                return True

            # Download WP-CLI
            self.debug.info("wp-cli.phar not exists , downloading WordPress CLI...")
            validate_directory(os.path.dirname(wp_cli_path))

            downloader = Downloader(
                url="https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar",
                desc="WordPress CLI"
            )
            downloader.download_to(wp_cli_path)

            # Make it executable
            os.chmod(wp_cli_path, 0o755)
            self.debug.success("WordPress CLI downloaded successfully")

            return True
        except Exception as e:
            self.debug.error(f"Failed to ensure WordPress CLI: {e}")
            return False

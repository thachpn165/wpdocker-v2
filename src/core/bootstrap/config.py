"""
Configuration bootstrap module.

This module handles initial configuration of the system, including
user preferences, timezone, webserver choice, and database version.
"""

import questionary
import jsons
from jsons.exceptions import DeserializationError

from src.common.logging import Debug, log_call
from src.core.bootstrap.base import BaseBootstrap
from src.common.config.manager import ConfigManager
from src.core.models.core_config import CoreConfig


@log_call
class ConfigBootstrap(BaseBootstrap):
    """Handles core configuration initialization."""
    debug = Debug("ConfigBootstrap")

    def __init__(self) -> None:
        """Initialize configuration bootstrap."""
        super().__init__("ConfigBootstrap")
        self.config_manager = ConfigManager()

    def is_bootstrapped(self) -> bool:
        """
        Check if configuration is already bootstrapped.

        Returns:
            bool: True if configuration is already bootstrapped, False otherwise
        """
        full_config = self.config_manager.get()

        # If there is no "core" key in config, definitely needs bootstrap
        if "core" not in full_config:
            self.debug.info("Key 'core' does not exist in config.json")
            return False

        raw_core = full_config.get("core", {})

        # Check if core config has all required fields
        required_fields = ["channel", "timezone", "webserver", "lang"]
        for field in required_fields:
            if field not in raw_core:
                self.debug.info(f"Missing configuration field {field} in core config")
                return False

        # Check if core configuration is valid
        try:
            jsons.load(raw_core, CoreConfig)
            return True
        except DeserializationError:
            return False
        except Exception as e:
            self.debug.error(f"Error checking core config: {e}")
            return False

    def check_prerequisites(self) -> bool:
        """
        Check if prerequisites for configuration bootstrap are met.

        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        # No specific prerequisites for configuration bootstrap
        return True

    def execute_bootstrap(self) -> bool:
        """
        Execute the configuration bootstrap process.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.debug.info("Initializing system configuration...")

            # Ask user for required information
            lang = questionary.select(
                "Select language:",
                choices=["vi", "en"]
            ).ask()

            if lang is None:
                self.debug.error("User cancelled language selection")
                return False

            channel = questionary.select(
                "Select release channel:",
                choices=["stable", "nightly", "dev"]
            ).ask()

            if channel is None:
                self.debug.error("User cancelled channel selection")
                return False

            timezone = questionary.text(
                "Enter system timezone (e.g., Asia/Ho_Chi_Minh):",
                default="Asia/Ho_Chi_Minh"
            ).ask()

            if timezone is None:
                self.debug.error("User cancelled timezone entry")
                return False

            webserver = questionary.select(
                "Select webserver:",
                choices=["nginx", "apache"]
            ).ask()

            if webserver is None:
                self.debug.error("User cancelled webserver selection")
                return False

            # Create configuration - removed mysql_version
            core_config = CoreConfig(
                lang=lang,
                channel=channel,
                timezone=timezone,
                webserver=webserver,
                containers=[]
            )

            # Save configuration
            self.config_manager.update_key("core", jsons.dump(core_config))
            self.config_manager.save()

            self.debug.success("Core configuration initialized successfully")
            return True
        except Exception as e:
            self.debug.error(f"Failed to initialize core configuration: {e}")
            # Do not create default configuration, require user to set up manually
            self.debug.info("User needs to set up configuration manually")
            return False

    def mark_bootstrapped(self) -> None:
        """Mark configuration as bootstrapped."""
        # Configuration bootstrap is marked by the presence of valid core config
        pass


"""
System bootstrap module.

This module handles the configuration of system-level settings like timezone.
"""

import platform
import subprocess
import questionary
from typing import Dict, Any, Optional

from src.common.logging import log_call
from src.core.bootstrap.base import BaseBootstrap
from src.core.config.manager import ConfigManager


class SystemBootstrap(BaseBootstrap):
    """Manages system-level bootstrap operations."""
    
    def __init__(self) -> None:
        """Initialize the system bootstrap component."""
        super().__init__("SystemBootstrap")
        self.config = ConfigManager()
        
    def is_bootstrapped(self) -> bool:
        """
        Check if system is already bootstrapped.
        
        Returns:
            bool: True if system is bootstrapped, False otherwise
        """
        core_config = self.config.get().get("core", {})
        return bool(core_config.get("timezone"))
        
    def check_prerequisites(self) -> bool:
        """
        Check if prerequisites for system bootstrap are met.
        
        Returns:
            bool: True if prerequisites are met, False otherwise
        """
        # No specific prerequisites for system bootstrap
        return True
        
    def execute_bootstrap(self) -> bool:
        """
        Execute the system bootstrap process.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self._ensure_core_timezone()
        
    def mark_bootstrapped(self) -> None:
        """Mark system as bootstrapped."""
        # No specific marking needed as the timezone itself 
        # serves as the bootstrap marker
        pass
    
    @log_call
    def _ensure_core_timezone(self) -> bool:
        """
        Ensure timezone is configured and set in the system.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if timezone is already set
        core_config = self.config.get().get("core", {})
        timezone = core_config.get("timezone")
        
        # Prompt for timezone if not set
        if not timezone:
            timezone = questionary.text(
                "Enter timezone (TZ database format, e.g., Asia/Ho_Chi_Minh):"
            ).ask()
            
            # Update configuration
            core_config["timezone"] = timezone
            self.config.update_key("core", core_config)
            self.config.save()
        
        # Set system timezone (Linux only)
        system_type = platform.system()
        if system_type == "Linux":
            try:
                subprocess.run(["timedatectl", "set-timezone", timezone], check=True)
                self.debug.success(f"System timezone set to {timezone}")
            except FileNotFoundError:
                self.debug.warn("timedatectl not found, skipping system timezone setting")
            except subprocess.CalledProcessError as e:
                self.debug.error(f"Failed to set system timezone: {e}")
                return False
        else:
            self.debug.info(f"Running on {system_type}, skipping system timezone setting")
            
        return True
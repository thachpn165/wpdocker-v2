"""
Bootstrap controller.

This module orchestrates the bootstrap process, executing each bootstrap
component in the correct order.
"""

from typing import List, Type

from src.common.logging import Debug, log_call
from src.core.bootstrap.base import BaseBootstrap
from src.core.bootstrap.config import ConfigBootstrap
from src.core.bootstrap.system import SystemBootstrap
from src.core.bootstrap.docker import DockerBootstrap
from src.core.bootstrap.mysql import MySQLBootstrap
from src.core.bootstrap.webserver import get_webserver_bootstrap
from src.core.bootstrap.wpcli import WPCLIBootstrap
from src.core.bootstrap.redis import RedisBootstrap
from src.core.bootstrap.rclone import RcloneBootstrap
from src.core.bootstrap.misc import MiscBootstrap


class BootstrapController:
    """
    Manages the sequential bootstrapping of all system components.
    
    This controller follows the Facade pattern, providing a single interface
    to the complex bootstrapping process.
    """
    
    def __init__(self) -> None:
        """Initialize the bootstrap controller."""
        self.debug = Debug("BootstrapController")
        
        # Define bootstrap sequence
        self.bootstrap_sequence = [
            ConfigBootstrap,
            SystemBootstrap,
            DockerBootstrap,
            MySQLBootstrap,
            get_webserver_bootstrap,
            WPCLIBootstrap,
            RedisBootstrap,
            RcloneBootstrap,
            MiscBootstrap
        ]
        
    @log_call
    def run_bootstrap(self) -> bool:
        """
        Run the complete bootstrap process.
        
        Returns:
            bool: True if all components bootstrapped successfully, False otherwise
        """
        self.debug.info("Starting bootstrap sequence")
        
        result = True
        for bootstrap_class in self.bootstrap_sequence:
            if callable(bootstrap_class) and not isinstance(bootstrap_class, type):
                bootstrap = bootstrap_class()
            else:
                bootstrap = bootstrap_class()
            component_name = bootstrap.__class__.__name__
            
            self.debug.info(f"Bootstrapping {component_name}")
            if not bootstrap.bootstrap():
                self.debug.error(f"Failed to bootstrap {component_name}")
                result = False
                break
                
        if result:
            self.debug.success("Bootstrap sequence completed successfully")
        else:
            self.debug.error("Bootstrap sequence failed")
            
        return result
        
    @log_call
    def run_specific_bootstrap(self, component_name: str) -> bool:
        """
        Run a specific bootstrap component.
        
        Args:
            component_name: Name of the bootstrap component to run
            
        Returns:
            bool: True if successful, False otherwise
        """
        for bootstrap_class in self.bootstrap_sequence:
            if bootstrap_class.__name__ == component_name:
                bootstrap = bootstrap_class()
                return bootstrap.bootstrap()
                
        self.debug.error(f"Bootstrap component not found: {component_name}")
        return False
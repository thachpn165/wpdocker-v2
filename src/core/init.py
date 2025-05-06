"""
Core initialization module.

This module handles the initialization of the core system components,
loading environment variables, and orchestrating the bootstrap process.
"""

import os
import sys
import importlib
from typing import Dict, Any, List, Optional

from src.common.logging import Debug, log_call
from src.common.utils.environment import load_environment
from src.core.bootstrap.controller import BootstrapController


class SystemInitializer:
    """
    Manages the initialization of the core system.
    
    This class is responsible for setting up the environment,
    checking dependencies, and orchestrating the bootstrap process.
    """
    
    def __init__(self) -> None:
        """Initialize the system initializer."""
        self.debug = Debug("SystemInitializer")
        self.required_modules = {
            "python-on-whales": "python-on-whales",
            "questionary": "questionary",
            "rich": "rich",
            "requests": "requests",
            "passlib": "passlib",
            "bcrypt": "bcrypt",
            "colorama": "colorama",
            "python-dotenv": "python-dotenv"
        }
        
    @log_call
    def initialize(self) -> bool:
        """
        Initialize the system.
        
        This method:
        1. Checks and installs required Python modules
        2. Loads environment variables
        3. Runs the bootstrap process
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        self.debug.info("Starting system initialization")
        
        # Check and install required modules
        if not self._check_and_install_modules():
            self.debug.error("Failed to install required modules")
            return False
            
        # Load environment variables
        if not self._load_environment():
            self.debug.error("Failed to load environment variables")
            return False
            
        # Run bootstrap process
        bootstrap_controller = BootstrapController()
        if not bootstrap_controller.run_bootstrap():
            self.debug.error("Bootstrap process failed")
            return False
            
        self.debug.success("System initialization completed successfully")
        return True
        
    @log_call
    def _check_and_install_modules(self) -> bool:
        """
        Check if required modules are installed and install if missing.
        
        Returns:
            bool: True if all modules are available, False otherwise
        """
        missing_modules = []
        
        for module_name, package_name in self.required_modules.items():
            try:
                importlib.import_module(module_name)
            except ImportError:
                missing_modules.append(package_name)
                
        if missing_modules:
            self.debug.warn(f"Installing missing modules: {', '.join(missing_modules)}")
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_modules)
                self.debug.success("Successfully installed missing modules")
            except Exception as e:
                self.debug.error(f"Failed to install modules: {e}")
                return False
                
        return True
        
    @log_call
    def _load_environment(self) -> bool:
        """
        Load environment variables from core.env file.
        
        Returns:
            bool: True if environment loaded successfully, False otherwise
        """
        try:
            # Find the core.env file relative to the script location
            install_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            
            # Check the root directory first (new location)
            root_env_file = os.path.join(install_dir, 'core.env')
            root_env_sample = os.path.join(install_dir, 'core.env.sample')
            
            # Create from sample if needed
            if not os.path.exists(root_env_file) and os.path.exists(root_env_sample):
                try:
                    self.debug.info(f"Creating core.env from sample...")
                    import shutil
                    shutil.copy2(root_env_sample, root_env_file)
                    self.debug.success(f"Created core.env from sample template")
                except Exception as e:
                    self.debug.error(f"Failed to create core.env from sample: {e}")
            
            # Fallback to src/config directory
            config_env_file = os.path.join(install_dir, 'src', 'config', 'core.env')
            
            # Legacy location
            legacy_env_file = os.path.join(install_dir, 'core', 'core.env')
            
            # Use the first env file found
            if os.path.exists(root_env_file):
                env_file = root_env_file
            elif os.path.exists(config_env_file):
                env_file = config_env_file
            elif os.path.exists(legacy_env_file):
                env_file = legacy_env_file
            else:
                self.debug.error("Environment file not found in any known location")
                return False
                
            # Load the environment
            load_environment(env_file)
            self.debug.info(f"Environment loaded from {env_file}")
            
            return True
        except Exception as e:
            self.debug.error(f"Failed to load environment: {e}")
            return False


# Singleton instance for easy access
system_initializer = SystemInitializer()


@log_call
def initialize_system() -> bool:
    """
    Initialize the system.
    
    This is the main entry point for system initialization.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    return system_initializer.initialize()
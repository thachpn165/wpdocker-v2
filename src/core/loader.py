"""
Core system loader.

This module is responsible for the initial system loading,
including environment variable setup and dependency checking.
"""

import os
import sys
import importlib
from typing import Dict, Optional

from src.common.logging import Debug, log_call
from src.common.utils.environment import env, load_environment


class CoreLoader:
    """
    Manages the loading of core system dependencies and environment.

    This is the first component that runs during system startup and
    prepares the environment for other components.
    """

    _instance = None

    def __new__(cls) -> 'CoreLoader':
        """
        Singleton pattern to ensure only one loader exists.

        Returns:
            CoreLoader: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super(CoreLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the core loader."""
        if self._initialized:
            return

        self._initialized = True
        self.debug = Debug("CoreLoader")
        self.required_modules = {
            "python_on_whales": "python-on-whales",
            "questionary": "questionary",
            "rich": "rich",
            "requests": "requests",
            "passlib": "passlib",
            "bcrypt": "bcrypt",
            "colorama": "colorama",
            "python-dotenv": "python-dotenv",
            "tabulate": "tabulate"
        }

    @log_call
    def load(self) -> bool:
        """
        Load the core system.

        This method:
        1. Installs required Python modules
        2. Loads environment variables

        Returns:
            bool: True if loading successful, False otherwise
        """
        self.debug.info("Starting core system loading")

        # Check and install required modules
        if not self._check_and_install_modules():
            self.debug.error("Failed to install required modules")
            return False

        # Load environment variables
        env_file = self._find_env_file()
        if not env_file:
            self.debug.error("Failed to find environment file")
            return False

        if not self._load_environment(env_file):
            self.debug.error("Failed to load environment variables")
            return False

        self.debug.success("Core system loaded successfully")
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
                self.debug.debug(f"Module found: {module_name}")
            except ImportError:
                missing_modules.append(package_name)
                self.debug.debug(f"Module missing: {module_name}")

        if missing_modules:
            self.debug.warn(
                f"Installing missing modules: {', '.join(missing_modules)}")
            try:
                import subprocess
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install"] + missing_modules)
                self.debug.success("Successfully installed missing modules")
            except Exception as e:
                self.debug.error(f"Failed to install modules: {e}")
                return False

        return True

    @log_call
    def _find_env_file(self) -> Optional[str]:
        """
        Find the core.env file.

        If core.env doesn't exist but core.env.sample does, it will create
        core.env from the sample.

        Returns:
            Optional[str]: Path to env file or None if not found
        """
        # Get the project root directory (2 levels up from this file)
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../..'))

        # Primary location: project root
        root_env = os.path.join(project_root, "core.env")
        root_env_sample = os.path.join(project_root, "core.env.sample")

        # Check if we should create core.env from sample
        if not os.path.exists(root_env) and os.path.exists(root_env_sample):
            try:
                self.debug.info(f"Creating core.env from sample...")
                import shutil
                shutil.copy2(root_env_sample, root_env)
                self.debug.success(f"Created core.env from sample template")
            except Exception as e:
                self.debug.error(f"Failed to create core.env from sample: {e}")

        # Now check for the file again
        if os.path.exists(root_env):
            return root_env

        # Secondary location: src/config directory
        config_env = os.path.join(project_root, "src", "config", "core.env")
        config_env_sample = os.path.join(
            project_root, "src", "config", "core.env.sample")

        # Check if we should create config/core.env from sample
        if not os.path.exists(config_env) and os.path.exists(config_env_sample):
            try:
                self.debug.info(f"Creating src/config/core.env from sample...")
                import shutil
                shutil.copy2(config_env_sample, config_env)
                self.debug.success(
                    f"Created src/config/core.env from sample template")
            except Exception as e:
                self.debug.error(
                    f"Failed to create src/config/core.env from sample: {e}")

        if os.path.exists(config_env):
            return config_env

        # Fallback to current directory
        if os.path.exists("core.env"):
            return os.path.abspath("core.env")

        # Check in standard locations for backward compatibility
        standard_locations = [
            os.path.join(project_root, "config", "core.env"),
            os.path.join(project_root, "core", "core.env")
        ]

        for location in standard_locations:
            if os.path.exists(location):
                return location

        return None

    @log_call
    def _load_environment(self, env_file: str) -> bool:
        """
        Load environment variables from file.

        Args:
            env_file: Path to environment file

        Returns:
            bool: True if environment loaded successfully, False otherwise
        """
        try:
            load_environment(env_file)
            self.debug.info(f"Environment loaded from {env_file}")

            # Configure debug mode
            debug_mode = env.get("DEBUG_MODE", "false").lower() in (
                "true", "1", "yes")
            if debug_mode:
                self.debug.info("Debug mode enabled")

            return True
        except Exception as e:
            self.debug.error(f"Failed to load environment: {e}")
            return False


# Singleton instance for easy access
core_loader = CoreLoader()


@log_call
def load_core() -> bool:
    """
    Load the core system.

    This is the main entry point for system loading.

    Returns:
        bool: True if loading successful, False otherwise
    """
    return core_loader.load()

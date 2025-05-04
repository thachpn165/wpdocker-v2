"""
Base class for PHP extensions.

This module provides a base class that all PHP extension implementations
must inherit from, ensuring consistent interface and behavior.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from src.common.logging import log_call, debug, info, warn, error
from src.features.website.utils import get_site_config, set_site_config


class BaseExtension(ABC):
    """Base class for PHP extensions."""
    
    @property
    @abstractmethod
    def id(self) -> str:
        """
        Get the unique identifier for this extension.
        
        Returns:
            str: Extension ID
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the human-readable name for this extension.
        
        Returns:
            str: Extension name
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get a description of this extension.
        
        Returns:
            str: Extension description
        """
        pass
    
    @property
    def requires_compilation(self) -> bool:
        """
        Whether this extension requires compilation.
        
        Returns:
            bool: True if compilation is required, False otherwise
        """
        return False
    
    @property
    def php_version_constraints(self) -> Optional[Dict[str, List[str]]]:
        """
        Get PHP version constraints for this extension.
        
        Returns:
            Optional[Dict[str, List[str]]]: Dictionary mapping constraint types
                                           ("requires", "incompatible") to lists of
                                           PHP versions, or None if no constraints
        """
        return None
    
    @log_call
    def check_compatibility(self, php_version: str) -> bool:
        """
        Check if this extension is compatible with a specific PHP version.
        
        Args:
            php_version: PHP version to check
            
        Returns:
            bool: True if compatible, False otherwise
        """
        constraints = self.php_version_constraints
        if not constraints:
            return True
        
        # Check required versions
        requires = constraints.get("requires", [])
        if requires and php_version not in requires:
            return False
        
        # Check incompatible versions
        incompatible = constraints.get("incompatible", [])
        if incompatible and php_version in incompatible:
            return False
        
        return True
    
    @abstractmethod
    def install(self, domain: str) -> bool:
        """
        Install this extension for a website.
        
        Args:
            domain: Website domain name
            
        Returns:
            bool: True if installation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def uninstall(self, domain: str) -> bool:
        """
        Uninstall this extension for a website.
        
        Args:
            domain: Website domain name
            
        Returns:
            bool: True if uninstallation was successful, False otherwise
        """
        pass
    
    @log_call
    def update_config(self, domain: str) -> bool:
        """
        Update website configuration to reflect extension installation.
        
        Args:
            domain: Website domain name
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        site_config = get_site_config(domain)
        if not site_config or not hasattr(site_config, 'php') or not site_config.php:
            error(f"❌ PHP configuration not found for website {domain}")
            return False
        
        # Initialize extensions list if it doesn't exist
        if not site_config.php.php_installed_extensions:
            site_config.php.php_installed_extensions = []
        
        # Add extension to list if not already present
        if self.id not in site_config.php.php_installed_extensions:
            site_config.php.php_installed_extensions.append(self.id)
            set_site_config(domain, site_config)
            info(f"📝 Added {self.name} to installed extensions for {domain}")
        
        return True
    
    @log_call
    def remove_from_config(self, domain: str) -> bool:
        """
        Remove extension from website configuration after uninstallation.
        
        Args:
            domain: Website domain name
            
        Returns:
            bool: True if removal was successful, False otherwise
        """
        site_config = get_site_config(domain)
        if not site_config or not hasattr(site_config, 'php') or not site_config.php:
            error(f"❌ PHP configuration not found for website {domain}")
            return False
        
        # Skip if no extensions list or extension not in list
        if not site_config.php.php_installed_extensions or self.id not in site_config.php.php_installed_extensions:
            return True
        
        # Remove extension from list
        site_config.php.php_installed_extensions.remove(self.id)
        set_site_config(domain, site_config)
        info(f"📝 Removed {self.name} from installed extensions for {domain}")
        
        return True
    
    def post_install(self, domain: str) -> None:
        """
        Perform post-installation actions.
        
        This method is called after installation and config update.
        Override in subclasses if needed.
        
        Args:
            domain: Website domain name
        """
        pass
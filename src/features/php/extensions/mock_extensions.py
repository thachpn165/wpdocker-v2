"""
Mock PHP extensions for testing purposes.

This module provides mock PHP extensions that can be used for testing
when no real extensions are available or compatible.
"""

from typing import Dict, List, Optional

from src.common.logging import log_call, info, debug, warn, error
from src.features.php.extensions.base import BaseExtension
from src.features.php.extensions.registry import register_extension
from src.common.containers.container import Container


class XdebugExtension(BaseExtension):
    """Xdebug extension implementation."""
    
    @property
    def id(self) -> str:
        return "xdebug"
    
    @property
    def name(self) -> str:
        return "Xdebug"
    
    @property
    def description(self) -> str:
        return "PHP debugging and development aid providing code coverage, debugging, profiling, and tracing"
    
    @property
    def requires_compilation(self) -> bool:
        return True
    
    @property
    def php_version_constraints(self) -> Optional[Dict[str, List[str]]]:
        # Xdebug supports a wide range of PHP versions
        return None
    
    @log_call
    def install(self, domain: str) -> bool:
        """
        Install Xdebug extension for a website.
        
        Args:
            domain: Website domain name
            
        Returns:
            bool: True if installation was successful, False otherwise
        """
        try:
            from src.features.php.client import init_php_client
            container = init_php_client(domain)
            
            # Install Xdebug through PECL
            info("📦 Installing Xdebug extension...")
            container.exec([
                "bash", "-c",
                "apt-get update && " +
                "apt-get install -y php-pear php-dev && " +
                "pecl install xdebug"
            ], user="root")
            
            # Update PHP configuration
            from src.common.utils.environment import env
            php_ini = f"{env['SITES_DIR']}/{domain}/php/php.ini"
            
            with open(php_ini, "a") as f:
                f.write("\n; Xdebug configuration\n")
                f.write("zend_extension=xdebug.so\n")
                f.write("xdebug.mode=develop,debug\n")
                f.write("xdebug.client_host=host.docker.internal\n")
                f.write("xdebug.client_port=9003\n")
                f.write("xdebug.start_with_request=yes\n")
            
            # Restart PHP container
            container.restart()
            
            info(f"✅ Xdebug installed successfully for {domain}.")
            return True
        except Exception as e:
            error(f"❌ Error installing Xdebug: {e}")
            return False
    
    @log_call
    def uninstall(self, domain: str) -> bool:
        """
        Uninstall Xdebug extension for a website.
        
        Args:
            domain: Website domain name
            
        Returns:
            bool: True if uninstallation was successful, False otherwise
        """
        try:
            from src.features.php.client import init_php_client
            from src.common.utils.environment import env
            
            # Update PHP configuration
            php_ini = f"{env['SITES_DIR']}/{domain}/php/php.ini"
            
            with open(php_ini, "r") as f:
                lines = [line for line in f if "xdebug" not in line.lower()]
            
            with open(php_ini, "w") as f:
                f.writelines(lines)
            
            # Restart PHP container
            container = init_php_client(domain)
            container.restart()
            
            info(f"✅ Xdebug uninstalled successfully for {domain}.")
            return True
        except Exception as e:
            error(f"❌ Error uninstalling Xdebug: {e}")
            return False


class OpCacheExtension(BaseExtension):
    """OPCache extension implementation."""
    
    @property
    def id(self) -> str:
        return "opcache"
    
    @property
    def name(self) -> str:
        return "OPCache"
    
    @property
    def description(self) -> str:
        return "Improves PHP performance by storing precompiled script bytecode in shared memory"
    
    @log_call
    def install(self, domain: str) -> bool:
        """
        Install OPCache extension for a website.
        
        Args:
            domain: Website domain name
            
        Returns:
            bool: True if installation was successful, False otherwise
        """
        try:
            from src.common.utils.environment import env
            
            # OPCache is already included in PHP, just need to enable it
            php_ini = f"{env['SITES_DIR']}/{domain}/php/php.ini"
            
            with open(php_ini, "a") as f:
                f.write("\n; OPCache configuration\n")
                f.write("zend_extension=opcache.so\n")
                f.write("opcache.enable=1\n")
                f.write("opcache.memory_consumption=128\n")
                f.write("opcache.interned_strings_buffer=8\n")
                f.write("opcache.max_accelerated_files=4000\n")
                f.write("opcache.revalidate_freq=60\n")
                f.write("opcache.fast_shutdown=1\n")
                f.write("opcache.enable_cli=1\n")
            
            # Restart PHP container
            from src.features.php.client import init_php_client
            container = init_php_client(domain)
            container.restart()
            
            info(f"✅ OPCache installed successfully for {domain}.")
            return True
        except Exception as e:
            error(f"❌ Error installing OPCache: {e}")
            return False
    
    @log_call
    def uninstall(self, domain: str) -> bool:
        """
        Uninstall OPCache extension for a website.
        
        Args:
            domain: Website domain name
            
        Returns:
            bool: True if uninstallation was successful, False otherwise
        """
        try:
            from src.common.utils.environment import env
            
            # Update PHP configuration
            php_ini = f"{env['SITES_DIR']}/{domain}/php/php.ini"
            
            with open(php_ini, "r") as f:
                lines = [line for line in f if "opcache" not in line.lower()]
            
            with open(php_ini, "w") as f:
                f.writelines(lines)
            
            # Restart PHP container
            from src.features.php.client import init_php_client
            container = init_php_client(domain)
            container.restart()
            
            info(f"✅ OPCache uninstalled successfully for {domain}.")
            return True
        except Exception as e:
            error(f"❌ Error uninstalling OPCache: {e}")
            return False


# Register the mock extensions in the registry
register_extension("xdebug", XdebugExtension)
register_extension("opcache", OpCacheExtension)
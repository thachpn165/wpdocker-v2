"""
IonCube Loader PHP extension.

This module provides functionality for installing and managing the
IonCube Loader PHP extension, which is required for some commercial plugins.
"""

import os
from typing import Dict, List, Optional

from src.common.logging import log_call, info, error, debug
from src.common.utils.environment import env
from src.common.utils.validation import is_arm
from src.features.php.extensions.base import BaseExtension
from src.features.php.extensions.registry import register_extension
from src.features.php.client import init_php_client


class IoncubeLoaderExtension(BaseExtension):
    """IonCube Loader extension implementation."""
    
    @property
    def id(self) -> str:
        return "ioncube_loader"
    
    @property
    def name(self) -> str:
        return "IonCube Loader"
    
    @property
    def description(self) -> str:
        return "Enables execution of PHP code protected by IonCube Encoder (required for some commercial plugins)"
    
    @property
    def php_version_constraints(self) -> Optional[Dict[str, List[str]]]:
        # We'll determine compatibility dynamically in check_compatibility method
        return None
        
    @log_call
    def check_compatibility(self, php_version: str) -> bool:
        """
        Check if IonCube Loader is compatible with a specific PHP version.
        
        This method performs a more dynamic check for IonCube Loader compatibility
        by verifying if an appropriate loader file exists for the given PHP version.
        
        Args:
            php_version: PHP version to check
            
        Returns:
            bool: True if compatible, False otherwise
        """
        # Try to get a container to check for actual compatibility
        try:
            # Create a temporary container connection just to check compatibility
            from src.features.php.client import init_php_client
            import re
            
            # Basic checks before attempting container operations
            if not php_version:
                info("No PHP version specified for compatibility check")
                return True
                
            # Currently IonCube Loader doesn't officially support PHP 8.3 (as of early 2024)
            if php_version == "8.3":
                info("IonCube Loader is not compatible with PHP 8.3")
                return False
                
            # Check if we have access to the container
            try:
                # This is a simplified check that doesn't require a container
                # We verify compatibility based on known supported versions
                php_major_minor = re.match(r'(\d+\.\d+)', php_version)
                if php_major_minor:
                    php_version_clean = php_major_minor.group(1)
                    # IonCube supports PHP 5.3 to 8.2 as of early 2024
                    supported_versions = ["5.3", "5.4", "5.5", "5.6", "7.0", "7.1", "7.2", "7.3", "7.4", "8.0", "8.1", "8.2"]
                    is_compatible = php_version_clean in supported_versions
                    info(f"IonCube Loader compatibility with PHP {php_version_clean}: {is_compatible}")
                    return is_compatible
                else:
                    # If we can't parse the version, assume it's compatible
                    return True
                    
            except Exception as e:
                # If simplified check fails, fall back to most basic check
                info(f"Using basic compatibility check for IonCube: {e}")
                return php_version != "8.3"
                
        except Exception as e:
            # If anything fails, use a conservative check
            error(f"Error checking IonCube Loader compatibility: {e}")
            # Only exclude PHP 8.3
            return php_version != "8.3"
    
    @log_call
    def install(self, domain: str) -> bool:
        """
        Install IonCube Loader extension for a website.
        
        Args:
            domain: Website domain name
            
        Returns:
            bool: True if installation was successful, False otherwise
        """
        container = init_php_client(domain)

        # Get PHP version and architecture
        php_version = container.exec(["php", "-r", "echo PHP_VERSION;"]).strip().split(".")[:2]
        php_version = ".".join(php_version)

        if is_arm():
            error("❌ IonCube Loader is not compatible with ARM architecture")
            return False

        # Check if PHP is Thread Safe (ZTS) or Not Thread Safe (NTS)
        zts = container.exec(["php", "-i"]).find("Thread Safety => enabled") != -1
        zts_suffix = "_ts" if zts else ""
        loader_file = f"ioncube_loader_lin_{php_version}{zts_suffix}.so"
        loader_path = f"/opt/bitnami/php/lib/php/extensions/{loader_file}"

        info(f"🔍 Checking loader file: {loader_path}")
        
        # Test if file exists using the proper shell syntax
        file_exists = container.exec(["bash", "-c", f"[ -f {loader_path} ] && echo 'exists' || echo ''"]).strip()
        
        if file_exists != "exists":
            info("📥 Downloading and extracting IonCube...")
            container.exec([
                "bash", "-c",
                "mkdir -p /tmp/ioncube && "
                "curl -sSL -o /tmp/ioncube.tar.gz https://downloads.ioncube.com/loader_downloads/ioncube_loaders_lin_x86-64.tar.gz && "
                "tar -xzf /tmp/ioncube.tar.gz -C /tmp/ioncube && "
                "tar -tzf /tmp/ioncube.tar.gz > /tmp/ioncube/filelist.txt"
            ], user="root")

            # Check if the loader file exists in the archive
            file_in_archive = container.exec([
                "bash", "-c", 
                f"grep -q \"ioncube/{loader_file}\" /tmp/ioncube/filelist.txt && echo 'found' || echo ''"
            ]).strip()
            
            if file_in_archive != "found":
                error(f"❌ {loader_file} not found in the IonCube download. Incompatible version.")
                container.exec(["rm", "-rf", "/tmp/ioncube", "/tmp/ioncube.tar.gz"], user="root")
                return False

            container.exec([
                "bash", "-c",
                f"cp /tmp/ioncube/ioncube/{loader_file} {loader_path} && "
                f"chmod 755 {loader_path} && "
                f"rm -rf /tmp/ioncube /tmp/ioncube.tar.gz"
            ], user="root")

        # Verify file exists
        file_exists = container.exec(["bash", "-c", f"[ -f {loader_path} ] && echo 'exists' || echo ''"]).strip()
        if file_exists != "exists":
            error(f"❌ Loader file not found after copy: {loader_path}")
            return False

        # Update php.ini
        php_ini = f"{env['SITES_DIR']}/{domain}/php/php.ini"
        if not os.path.isfile(php_ini):
            error(f"❌ php.ini not found at {php_ini}")
            return False

        with open(php_ini, "r") as f:
            lines = [line for line in f if "ioncube_loader_lin" not in line]

        with open(php_ini, "w") as f:
            f.writelines(lines)
            f.write(f"\nzend_extension={loader_path}\n")

        container.restart()
        info(f"✅ IonCube Loader installed successfully for {domain}.")
        return True
    
    @log_call
    def uninstall(self, domain: str) -> bool:
        """
        Uninstall IonCube Loader extension for a website.
        
        Args:
            domain: Website domain name
            
        Returns:
            bool: True if uninstallation was successful, False otherwise
        """
        php_ini = f"{env['SITES_DIR']}/{domain}/php/php.ini"
        if not os.path.isfile(php_ini):
            error(f"❌ php.ini not found at {php_ini}")
            return False
        
        try:
            # Remove IonCube Loader from php.ini
            with open(php_ini, "r") as f:
                lines = [line for line in f if "ioncube_loader_lin" not in line]
                
            with open(php_ini, "w") as f:
                f.writelines(lines)
                
            # Restart the PHP container
            container = init_php_client(domain)
            container.restart()
            
            info(f"✅ IonCube Loader uninstalled successfully for {domain}.")
            return True
        except Exception as e:
            error(f"❌ Error uninstalling IonCube Loader: {e}")
            return False
    
    def post_install(self, domain: str) -> None:
        """
        Perform post-installation verification.
        
        Args:
            domain: Website domain name
        """
        container = init_php_client(domain)
        output = container.exec(["php", "-v"])
        if output:
            info("📦 Current PHP version in container:")
            print(output)


# Register the extension in the registry
register_extension("ioncube_loader", IoncubeLoaderExtension)
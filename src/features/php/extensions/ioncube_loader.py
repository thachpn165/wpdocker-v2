"""
IonCube Loader PHP extension.

This module provides functionality for installing and managing the
IonCube Loader PHP extension, which is required for some commercial plugins.

Note: IonCube Loader doesn't have version-specific installation files.
Instead, it provides a single archive containing .so files for all supported
PHP versions. The appropriate loader file is selected based on the PHP version
and architecture at installation time.
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
        return None
    
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
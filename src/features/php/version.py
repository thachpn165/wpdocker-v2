"""
PHP version management functionality.

This module provides functions for managing PHP versions in websites,
including changing versions and checking available versions.
"""

import os
import re
import requests
from typing import Optional, Dict, Any, List, Tuple

from rich.progress import Progress, SpinnerColumn, TextColumn

from src.common.logging import log_call, debug, error, info, warn
from src.common.utils.environment import env
from src.core.containers.compose import Compose
from src.features.website.utils import get_site_config, set_site_config
from src.features.website.models.site_config import SitePHP
from src.features.php.client import init_php_client
from src.features.php.utils import get_php_container_name, AVAILABLE_PHP_VERSIONS


# Constants for Docker Hub
BITNAMI_IMAGE_PREFIX = "bitnami/php-fpm"
DOCKER_HUB_URL = "https://hub.docker.com/v2/repositories/{image}/tags/{version}"


def validate_php_version(version: str) -> bool:
    """
    Validate PHP version format and availability.
    
    Args:
        version: PHP version to validate
        
    Returns:
        bool: True if version is valid and available, False otherwise
    """
    try:
        # Check format (e.g., 8.2, 8.2.0)
        if not re.match(r'^\d+\.\d+(\.\d+)?$', version):
            error(f"Invalid PHP version format: {version}")
            return False
            
        # Check if version is in available versions
        major_minor = '.'.join(version.split('.')[:2])
        if major_minor not in AVAILABLE_PHP_VERSIONS:
            error(f"PHP version {version} is not in supported versions: {AVAILABLE_PHP_VERSIONS}")
            return False
            
        # Check if version exists on Docker Hub
        image_url = DOCKER_HUB_URL.format(
            image=BITNAMI_IMAGE_PREFIX.replace('/', '%2F'),
            version=version
        )
        response = requests.get(image_url)
        if response.status_code != 200:
            error(f"PHP version {version} doesn't exist on Docker Hub!")
            return False
            
        return True
    except Exception as e:
        error(f"Error validating PHP version: {e}")
        return False


def check_version_compatibility(current_version: str, new_version: str) -> bool:
    """
    Check if new PHP version is compatible with current version.
    
    Args:
        current_version: Current PHP version
        new_version: New PHP version to check
        
    Returns:
        bool: True if versions are compatible, False otherwise
    """
    try:
        current_major = current_version.split('.')[0]
        new_major = new_version.split('.')[0]
        
        # Major version changes may have breaking changes
        if current_major != new_major:
            warn(f"⚠️ Major version change detected: {current_version} -> {new_version}")
            warn("This may have breaking changes. Please check compatibility.")
            return True
            
        # Minor version changes are usually safe
        current_minor = current_version.split('.')[1]
        new_minor = new_version.split('.')[1]
        if current_minor != new_minor:
            info(f"Minor version change: {current_version} -> {new_version}")
            return True
            
        # Patch version changes are always safe
        return True
    except Exception as e:
        error(f"Error checking version compatibility: {e}")
        return False


@log_call
def change_php_version(domain: str, php_version: str) -> bool:
    """
    Change PHP version for a website.
    
    This function updates the configuration, docker-compose file, and
    rebuilds the PHP container with the new version.
    
    Args:
        domain: Website domain name
        php_version: PHP version to change to (e.g., "8.2")
        
    Returns:
        bool: True if change was successful, False otherwise
    """
    try:
        # Validate version
        if not validate_php_version(php_version):
            return False
            
        # Get current version
        current_version = get_current_php_version(domain)
        if current_version:
            # Check compatibility
            if not check_version_compatibility(current_version, php_version):
                return False
                
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task(f"Changing PHP version to {php_version}...", total=None)

            # Update site config
            progress.update(task, description=f"Updating config for {domain}...")
            site_config = get_site_config(domain)
            if not site_config:
                progress.stop()
                error(f"❌ Configuration not found for domain: {domain}")
                return False

            if not hasattr(site_config, 'php') or not site_config.php:
                site_config.php = SitePHP(php_version=php_version, php_container=None, php_installed_extensions=[])
            else:
                site_config.php.php_version = php_version

            set_site_config(domain, site_config)
            info(f"📦 Updated config: PHP version → {php_version}")

            # Update docker-compose file
            compose_file_path = os.path.join(env["SITES_DIR"], domain, "docker-compose.php.yml")
            if not os.path.isfile(compose_file_path):
                progress.stop()
                error(f"❌ File not found: {compose_file_path}")
                return False

            progress.update(task, description="Updating docker-compose.php.yml...")
            with open(compose_file_path, "r") as f:
                lines = f.readlines()

            with open(compose_file_path, "w") as f:
                for line in lines:
                    if "bitnami/php-fpm:" in line:
                        indent = line[:len(line) - len(line.lstrip())]
                        f.write(f"{indent}image: bitnami/php-fpm:{php_version}\n")
                    else:
                        f.write(line)

            # Rebuild PHP container
            progress.update(task, description="Rebuilding PHP container...")
            container_name = get_php_container_name(domain)
            compose = Compose(name=f"{container_name}", output_path=compose_file_path)
            compose.down()
            compose.up(force_recreate=True)
            compose.ensure_ready()

        # Verify the new PHP version
        try:
            container = init_php_client(domain)
            output = container.exec(["php", "-v"])
            if output:
                print("\n📋 PHP Version Information:")
                print(output)
        except Exception as e:
            error(f"❌ Could not verify PHP version from container: {e}")

        info(f"✅ Successfully changed PHP version to {php_version} for {domain}.")

        # Restore previously installed extensions
        restore_php_extensions(domain)
        return True

    except Exception as e:
        error(f"❌ Error changing PHP version: {str(e)}")
        return False


@log_call
def get_current_php_version(domain: str) -> Optional[str]:
    """
    Get current PHP version for a website.
    
    Args:
        domain: Website domain name
        
    Returns:
        Optional[str]: Current PHP version if found, None otherwise
    """
    try:
        site_config = get_site_config(domain)
        if not site_config or not hasattr(site_config, 'php') or not site_config.php:
            return None
            
        return site_config.php.php_version
    except Exception as e:
        error(f"Error getting current PHP version: {e}")
        return None


@log_call
def restore_php_extensions(domain: str) -> None:
    """
    Restore PHP extensions after version change.
    
    Args:
        domain: Website domain name
    """
    from src.features.php.extensions.registry import EXTENSION_REGISTRY
    from src.features.php.extensions.manager import get_extension_instance
    
    site_config = get_site_config(domain)
    if not site_config or not hasattr(site_config, 'php') or not site_config.php:
        warn(f"⚠️ PHP configuration not found for website {domain}")
        return

    extensions = site_config.php.php_installed_extensions or []
    if not extensions:
        info(f"💤 Website {domain} doesn't have any PHP extensions installed.")
        return

    info(f"🔁 Restoring PHP extensions for {domain}...")
    for ext_id in extensions:
        try:
            if ext_id not in EXTENSION_REGISTRY:
                warn(f"⚠️ Extension '{ext_id}' is not in the supported extensions list.")
                continue

            ext = get_extension_instance(ext_id)
            ext.install(domain)
            ext.update_config(domain)
        except Exception as e:
            warn(f"⚠️ Error installing extension '{ext_id}': {e}")
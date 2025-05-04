"""
PHP utility functions.

This module provides utility functions for PHP operations,
including container management and version selection.
"""

from typing import Dict, List, Optional, Any

from python_on_whales import docker
import questionary

from src.common.logging import debug
from src.common.utils.validation import is_arm
from src.features.website.utils import get_site_config


def get_php_container_id_by_name(container_name: str) -> str:
    """
    Get PHP container ID by name.
    
    Args:
        container_name: Name of the PHP container
        
    Returns:
        Container ID
        
    Raises:
        ValueError: If container not found
    """
    containers = docker.container.list(
        all=True, filters={"name": container_name})
    if not containers:
        raise ValueError(
            f"PHP container not found with name {container_name}")
    return containers[0].id


def get_php_container_id(domain: str) -> str:
    """
    Get PHP container ID by domain.
    
    Args:
        domain: Website domain name
        
    Returns:
        Container ID
        
    Raises:
        ValueError: If container not found
    """
    site_config = get_site_config(domain)
    if not site_config or not hasattr(site_config, 'php') or not site_config.php or not site_config.php.php_container:
        raise ValueError(f"PHP Container ID not found for website {domain}")
    return site_config.php.php_container


def get_php_container_name(domain: str) -> str:
    """
    Get PHP container name for a domain.
    
    Args:
        domain: Website domain name
        
    Returns:
        Container name
    """
    # Simple naming convention - no need for complex lookup
    return f"{domain}-php"


# Available PHP versions
AVAILABLE_PHP_VERSIONS = [
    "8.0",
    "8.1",
    "8.2",
    "8.3",
]


def php_choose_version() -> str:
    """
    Display a prompt to choose PHP version.
    
    Returns:
        Selected PHP version
    """
    choices = []
    arm_system = is_arm()
    for ver in AVAILABLE_PHP_VERSIONS:
        label = f"{ver} (ARM not supported)" if arm_system and ver == "8.0" else ver
        choices.append({"name": label, "value": ver})

    selected = questionary.select(
        "🔢 Select PHP version:",
        choices=choices
    ).ask()

    debug(f"Selected PHP version: {selected}")
    return selected
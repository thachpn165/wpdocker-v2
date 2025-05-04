"""
PHP container client functionality.

This module provides functions for interacting with PHP containers,
including initialization and command execution.
"""

from typing import Optional, Dict, Any, List

from src.common.logging import log_call, error
from src.common.containers.container import Container
from src.features.php.utils import get_php_container_name


@log_call
def init_php_client(domain: str) -> Container:
    """
    Initialize a Container object for a website's PHP container.
    
    Automatically checks if the container exists before initializing.
    
    Args:
        domain: Website domain name
        
    Returns:
        Container: PHP container object
        
    Raises:
        ValueError: If container doesn't exist
    """
    container_name = get_php_container_name(domain)
    try:
        php_container = Container(container_name)

        if not php_container.exists():
            error(f"❌ PHP container doesn't exist with name: {container_name}")
            raise ValueError(f"Container doesn't exist for website: {domain}")

        return php_container
    except Exception as e:
        error(f"❌ Could not initialize PHP container for {domain}: {e}")
        raise


@log_call
def run_php_command(domain: str, command: List[str], user: str = "www-data") -> Optional[str]:
    """
    Run a command in the PHP container for a domain.
    
    Args:
        domain: Website domain name
        command: Command to run as a list of strings
        user: User to run command as (defaults to www-data)
        
    Returns:
        Optional[str]: Command output or None if error
    """
    try:
        container = init_php_client(domain)
        return container.exec(command, user=user)
    except Exception as e:
        error(f"❌ Error running PHP command for {domain}: {e}")
        return None


@log_call
def run_php_script(domain: str, php_code: str, user: str = "www-data") -> Optional[str]:
    """
    Run a PHP script string in the container.
    
    Args:
        domain: Website domain name
        php_code: PHP code to execute
        user: User to run command as (defaults to www-data)
        
    Returns:
        Optional[str]: Script output or None if error
    """
    try:
        container = init_php_client(domain)
        command = ["php", "-r", php_code]
        return container.exec(command, user=user)
    except Exception as e:
        error(f"❌ Error running PHP script for {domain}: {e}")
        return None